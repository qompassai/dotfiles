#!/usr/bin/env bash
# #################################################################
# /qompassai/.config/distcc/scripts/prepare.sh
# Qompass AI Prepare
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Qompass AI
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# #################################################################

# distcc-prepare.sh — make this device a distcc volunteer and client
# Copyright (C) 2026 Qompass AI, All rights reserved
# SPDX-License-Identifier: Apache-2.0
#
# Copy to every machine. Same commands everywhere:
#   ./distcc-prepare.sh install
#   ./distcc-prepare.sh up
#   eval "$(./distcc-prepare.sh env)"
#   make -j"$(distcc -j)"
#
# Every node is both roles. Volunteers advertise via Avahi (_distcc._tcp).
# Clients use DISTCC_HOSTS='localhost/N +zeroconf' so new servers appear
# without editing a host list. scan/recruit is optional if mDNS works.
#
# TCP distccd is unauthenticated remote compile. This script never passes
# --enable-tcp-insecure, never publishes 3632, and requires --allow-private.
# install never uses passwords; recruit never uses ssh without BatchMode keys.

set -eu
set -o pipefail

DISTCC_DIR="${DISTCC_DIR:-${HOME}/.distcc}"
CONF="${DISTCC_DIR}/cluster.conf"
HOSTS_FILE="${DISTCC_DIR}/hosts"
PID_FILE="${DISTCC_DIR}/distccd.pid"
LOG_FILE="${DISTCC_DIR}/distccd.log"
ENV_FILE="${DISTCC_DIR}/client.env"
SELF="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)/$(basename "${BASH_SOURCE[0]:-$0}")"
SSH_USER="${DISTCC_SSH_USER:-${USER:-$(id -un)}}"
SSH_OPTS=(-o BatchMode=yes -o ConnectTimeout=3 -o StrictHostKeyChecking=yes)
PORT_DEFAULT=3632

usage() {
	cat <<'EOF'
Usage: distcc-prepare.sh <command>

  install       Install distcc (+ avahi) with the native package manager
  up            Write config, start volunteer, write client.env
  down          Stop volunteer
  env           Print exports (eval "$(./distcc-prepare.sh env)")
  scan          Probe RFC1918 neighbors/mDNS for :3632; merge into HOSTS
  recruit HOST  SSH key: copy this script, up, then merge HOST
  status        Volunteer pid, HOSTS, distcc -j
  help

Environment: DISTCC_DIR  DISTCC_SSH_USER  DISTCC_FULL_SCAN=1
EOF
}

die() { printf '%s\n' "$*" >&2; exit 1; }
have() { command -v "$1" >/dev/null 2>&1; }

ncpus() {
	if have nproc; then nproc
	elif have getconf; then getconf _NPROCESSORS_ONLN
	else printf '%s\n' 2
	fi
}

is_private_v4() {
	local ip="${1%%/*}" a b
	a="${ip%%.*}"
	b="${ip#*.}"; b="${b%%.*}"
	[[ ${a} == 10 ]] && return 0
	[[ ${a} == 192 && ${b} == 168 ]] && return 0
	[[ ${a} == 172 && ${b} -ge 16 && ${b} -le 31 ]] && return 0
	return 1
}

pkg_install() {
	if have distccd && have distcc; then
		printf 'distcc already installed: %s\n' "$(distcc --version 2>/dev/null | head -n1 || echo distcc)"
		return 0
	fi
	local sudo=()
	[[ $(id -u) -eq 0 ]] || { have sudo && sudo=(sudo); }
	if have pacman; then
		"${sudo[@]}" pacman -S --needed --noconfirm distcc avahi nss-mdns
	elif have apt-get; then
		"${sudo[@]}" apt-get update -qq
		"${sudo[@]}" apt-get install -y distcc avahi-daemon avahi-utils
	elif have dnf; then
		"${sudo[@]}" dnf install -y distcc avahi avahi-tools
	elif have pkg && [[ -n ${PREFIX:-} || -d /data/data/com.termux ]]; then
		pkg install -y distcc avahi 2>/dev/null || pkg install -y distcc
	elif have brew; then
		brew install distcc
	else
		die 'No supported package manager. Install distcc (and avahi) yourself.'
	fi
	have distccd || die 'distccd still missing after install'
}

ensure_avahi() {
	if have systemctl; then
		systemctl is-active --quiet avahi-daemon 2>/dev/null \
			|| systemctl start avahi-daemon 2>/dev/null \
			|| true
	fi
}

write_config() {
	local cpus
	cpus="$(ncpus)"
	mkdir -p "${DISTCC_DIR}"
	umask 077
	if [[ ! -f ${CONF} ]]; then
		cat >"${CONF}" <<EOF
PORT=${PORT_DEFAULT}
LISTEN=0.0.0.0
ALLOW_PRIVATE=1
ALLOW=""
JOBS=0
NICE=10
JOB_LIFETIME=3600
LOG_LEVEL=warning
ZEROCONF=1
STATS=0
HOSTS="localhost/${cpus} +zeroconf"
MASQ_PATH=""
EOF
	fi
	if [[ ! -f ${HOSTS_FILE} ]]; then
		printf 'localhost/%s\n+zeroconf\n' "${cpus}" >"${HOSTS_FILE}"
	fi
	chmod 600 "${CONF}" "${HOSTS_FILE}" 2>/dev/null || true
}

load_conf() {
	[[ -f ${CONF} ]] || write_config
	# shellcheck disable=SC1090
	source "${CONF}"
	: "${PORT:=${PORT_DEFAULT}}"
	: "${LISTEN:=0.0.0.0}"
	: "${ALLOW_PRIVATE:=1}"
	: "${ALLOW:=}"
	: "${JOBS:=0}"
	: "${NICE:=10}"
	: "${JOB_LIFETIME:=3600}"
	: "${LOG_LEVEL:=warning}"
	: "${ZEROCONF:=1}"
	: "${STATS:=0}"
	: "${HOSTS:=localhost/$(ncpus) +zeroconf}"
	: "${MASQ_PATH:=}"
}

masq_dir() {
	local d
	[[ -n ${MASQ_PATH:-} && -d ${MASQ_PATH} ]] && { printf '%s\n' "${MASQ_PATH}"; return; }
	for d in /usr/lib/distcc/bin /usr/lib/distcc \
		"${PREFIX:-}/lib/distcc/bin" "${PREFIX:-}/lib/distcc" \
		/data/data/com.termux/files/usr/lib/distcc \
		/opt/homebrew/libexec/distcc /usr/local/libexec/distcc; do
		[[ -d ${d} ]] && { printf '%s\n' "${d}"; return; }
	done
}

print_env() {
	load_conf
	local masq jobs
	masq="$(masq_dir || true)"
	jobs="$(ncpus)"
	printf 'export DISTCC_DIR=%q\n' "${DISTCC_DIR}"
	printf 'export DISTCC_HOSTS=%q\n' "${HOSTS}"
	printf 'export DISTCC_FALLBACK=1\n'
	printf 'export DISTCC_SAVE_TEMPS=0\n'
	printf 'export DISTCC_VERBOSE=%q\n' "${DISTCC_VERBOSE:-0}"
	[[ -n ${masq} ]] && printf 'export PATH=%q\n' "${masq}:${PATH}"
	printf 'export MAKEFLAGS=%q\n' "-j$((jobs * 2))"
}

write_env() {
	print_env >"${ENV_FILE}"
	chmod 600 "${ENV_FILE}"
}

self_v4() {
	if have ip; then ip -4 -o addr show | awk '{print $4}' | cut -d/ -f1
	elif have ifconfig; then ifconfig | awk '/inet /{print $2}' | grep -v 127.0.0.1 || true
	fi
	printf '%s\n' 127.0.0.1
}

neighbors_v4() {
	have ip || return 0
	ip -4 neigh show | awk '/lladdr/ {print $1}'
}

local_cidrs() {
	have ip || return 0
	ip -4 -o addr show scope global | awk '{print $4}'
}

slash24() {
	local cidr="$1" ip mask a b c i
	ip="${cidr%%/*}"; mask="${cidr##*/}"
	[[ ${mask} == 24 ]] || return 0
	a="${ip%%.*}"; b="${ip#*.}"; b="${b%%.*}"; c="${ip#*.*.}"; c="${c%%.*}"
	for i in $(seq 1 254); do printf '%s.%s.%s.%s\n' "${a}" "${b}" "${c}" "${i}"; done
}

probe_port() {
	local ip="$1" port="$2"
	if have timeout; then
		timeout 0.2 bash -c "exec 3<>/dev/tcp/${ip}/${port}" >/dev/null 2>&1
	else
		bash -c "exec 3<>/dev/tcp/${ip}/${port}" >/dev/null 2>&1
	fi
}

avahi_v4() {
	have avahi-browse || return 0
	avahi-browse -artkpt 2>/dev/null | awk -F';' '
		$1=="=" && $3=="IPv4" && $5=="_distcc._tcp" {print $8}'
}

scan_hosts() {
	load_conf
	mkdir -p "${DISTCC_DIR}"
	local -A skip=()
	local ip cidr
	while read -r ip; do [[ -n ${ip} ]] && skip["${ip}"]=1; done < <(self_v4)
	local tmp found
	tmp="$(mktemp)"
	found="$(mktemp)"
	{
		neighbors_v4
		avahi_v4
		if [[ ${DISTCC_FULL_SCAN:-0} == 1 ]]; then
			while read -r cidr; do is_private_v4 "${cidr%%/*}" && slash24 "${cidr}"; done < <(local_cidrs)
		fi
	} | sort -u >"${tmp}"
	: >"${found}"
	while read -r ip; do
		[[ -z ${ip} || -n ${skip[${ip}]+x} ]] && continue
		is_private_v4 "${ip}" || continue
		probe_port "${ip}" "${PORT}" && printf '%s\n' "${ip}" >>"${found}"
	done <"${tmp}"
	rm -f "${tmp}"
	cat "${found}"
	mv -f "${found}" "${DISTCC_DIR}/discovered.txt"
}

merge_hosts_from() {
	load_conf
	local cpus ip slots line
	cpus="$(ncpus)"
	HOSTS="localhost/${cpus}"
	{
		printf 'localhost/%s\n' "${cpus}"
		while read -r ip; do
			[[ -z ${ip} ]] && continue
			slots=4
			if ssh "${SSH_OPTS[@]}" "${SSH_USER}@${ip}" true >/dev/null 2>&1; then
				slots="$(ssh "${SSH_OPTS[@]}" "${SSH_USER}@${ip}" 'nproc 2>/dev/null || echo 4')"
			fi
			line="${ip}/$((slots + 2)),lzo"
			HOSTS="${HOSTS} ${line}"
			printf '%s\n' "${line}"
		done
		printf '+zeroconf\n'
	} >"${HOSTS_FILE}"
	HOSTS="${HOSTS} +zeroconf"
	local t
	t="$(mktemp)"
	awk -v h="${HOSTS}" 'BEGIN{q="\""} /^HOSTS=/{print "HOSTS=" q h q; next} {print}' "${CONF}" >"${t}"
	mv -f "${t}" "${CONF}"
	chmod 600 "${CONF}" "${HOSTS_FILE}" 2>/dev/null || true
}

server_start() {
	load_conf
	have distccd || die 'distccd not in PATH; run: ./distcc-prepare.sh install'
	if [[ -f ${PID_FILE} ]] && kill -0 "$(cat "${PID_FILE}")" 2>/dev/null; then
		printf 'distccd already pid %s\n' "$(cat "${PID_FILE}")"
		return 0
	fi
	[[ ${ALLOW_PRIVATE} == 1 || -n ${ALLOW} ]] || die 'Refusing: set ALLOW_PRIVATE=1 or ALLOW=CIDR'
	local jobs
	if [[ ${JOBS} -gt 0 ]]; then jobs="${JOBS}"; else jobs=$(($(ncpus) + 2)); fi
	ensure_avahi
	local argv=(
		distccd --daemon
		--port "${PORT}"
		--listen "${LISTEN}"
		--jobs "${jobs}"
		--nice "${NICE}"
		--job-lifetime "${JOB_LIFETIME}"
		--pid-file "${PID_FILE}"
		--log-file "${LOG_FILE}"
		--log-level "${LOG_LEVEL}"
	)
	[[ ${ALLOW_PRIVATE} == 1 ]] && argv+=(--allow-private)
	local a
	# shellcheck disable=SC2086
	for a in ${ALLOW}; do argv+=(--allow "${a}"); done
	[[ ${ZEROCONF} == 1 ]] && argv+=(--zeroconf)
	[[ ${STATS} == 1 ]] && argv+=(--stats)
	"${argv[@]}"
	printf 'volunteer pid %s %s:%s jobs %s zeroconf=%s\n' \
		"$(cat "${PID_FILE}")" "${LISTEN}" "${PORT}" "${jobs}" "${ZEROCONF}"
}

server_stop() {
	[[ -f ${PID_FILE} ]] || return 0
	kill "$(cat "${PID_FILE}")" 2>/dev/null || true
	rm -f "${PID_FILE}"
}

cmd_up() {
	write_config
	server_start
	load_conf
	write_env
	printf 'client env: %s\n' "${ENV_FILE}"
	printf 'eval "$(%s env)"\n' "${SELF}"
}

cmd_scan() {
	write_config
	local list
	list="$(scan_hosts)"
	if [[ -z ${list} ]]; then
		printf 'No :%s listeners yet. Zeroconf still works after other nodes run up.\n' "${PORT_DEFAULT}"
		return 0
	fi
	printf '%s\n' "${list}" | merge_hosts_from
	write_env
	printf 'HOSTS updated. eval "$(%s env)"\n' "${SELF}"
}

cmd_recruit() {
	local host="$1"
	have ssh && have scp || die 'ssh/scp required'
	ssh "${SSH_OPTS[@]}" "${SSH_USER}@${host}" true \
		|| die "no SSH key for ${SSH_USER}@${host}"
	scp "${SSH_OPTS[@]}" "${SELF}" "${SSH_USER}@${host}:/tmp/distcc-prepare.sh"
	ssh "${SSH_OPTS[@]}" "${SSH_USER}@${host}" \
		"chmod 755 /tmp/distcc-prepare.sh && /tmp/distcc-prepare.sh up"
	printf '%s\n' "${host}" | merge_hosts_from
	write_env
}

cmd_status() {
	load_conf
	if [[ -f ${PID_FILE} ]] && kill -0 "$(cat "${PID_FILE}")" 2>/dev/null; then
		printf 'volunteer: pid %s\n' "$(cat "${PID_FILE}")"
	else
		printf 'volunteer: down\n'
	fi
	printf 'HOSTS=%s\n' "${HOSTS}"
	if have distcc; then
		DISTCC_DIR="${DISTCC_DIR}" DISTCC_HOSTS="${HOSTS}" distcc --show-hosts || true
		DISTCC_DIR="${DISTCC_DIR}" DISTCC_HOSTS="${HOSTS}" distcc -j || true
	fi
}

cmd="${1:-help}"
shift || true
case "${cmd}" in
install) pkg_install ;;
up) cmd_up ;;
down) server_stop ;;
env)
	write_config
	print_env
	;;
scan) cmd_scan ;;
recruit)
	[[ $# -ge 1 ]] || die 'recruit HOST'
	write_config
	cmd_recruit "$1"
	;;
status) cmd_status ;;
help | --help | -h) usage ;;
*)
	usage
	exit 1
	;;
esac
