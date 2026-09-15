#!/usr/bin/env bash
# #################################################################
# /qompassai/.config/distcc/scripts/recruit.sh
# Qompass AI Recruit
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

# distcc-cluster.sh — portable distcc client + volunteer kit
# Copyright (C) 2026 Qompass AI, All rights reserved
# SPDX-License-Identifier: Apache-2.0
#
# Copy this file to every machine. Run:  ./distcc-cluster.sh init
# Discover + recruit LAN volunteers you already control:
#   ./distcc-cluster.sh recruit-auto
# Volunteer:
#   ./distcc-cluster.sh server-start
# Client:
#   eval "$(./distcc-cluster.sh client-env)"
#   make -j"$(distcc -j)"
#
# TCP distccd is unauthenticated remote compile for anyone who can
# connect. This kit never passes --enable-tcp-insecure. Discovery
# only probes RFC1918/ULA. Recruitment only uses SSH BatchMode
# (existing keys). It will not install packages or guess passwords.
# Do not forward port 3632 to the internet.
#
# CLI reference: distcc / distccd 3.4
# Zeroconf: DISTCC_HOSTS=+zeroconf and distccd --zeroconf (Avahi).

set -eu
set -o pipefail

DISTCC_DIR="${DISTCC_DIR:-${HOME}/.distcc}"
CONF="${DISTCC_DIR}/cluster.conf"
HOSTS_FILE="${DISTCC_DIR}/hosts"
PID_FILE="${DISTCC_DIR}/distccd.pid"
LOG_FILE="${DISTCC_DIR}/distccd.log"
ENV_FILE="${DISTCC_DIR}/client.env"
FOUND_FILE="${DISTCC_DIR}/discovered.txt"
SELF="${BASH_SOURCE[0]:-$0}"
SSH_USER="${DISTCC_SSH_USER:-${USER:-$(id -un)}}"
SSH_OPTS=(-o BatchMode=yes -o ConnectTimeout=3 -o StrictHostKeyChecking=yes)

usage() {
	cat <<'EOF'
Usage: distcc-cluster.sh <command>

  init            Create DISTCC_DIR, cluster.conf, and hosts
  server-start    Start distccd as this machine's volunteer
  server-stop     SIGTERM the volunteer in the pid file
  client-env      Print export lines (eval "$(... client-env)")
  write-env       Write the same exports to $DISTCC_DIR/client.env
  discover        Find RFC1918 neighbors, mDNS distccd, port 3632
  recruit [HOST]  SSH BatchMode: init + server-start on HOST
  recruit-auto    discover, start distccd on SSH-reachable hosts,
                  merge 3632 volunteers into HOSTS
  status          Pid, port, hosts, distcc -j
  show-hosts      distcc --show-hosts
  help            This text

Environment: DISTCC_DIR (default ~/.distcc)
             DISTCC_SSH_USER (default $USER)
             DISTCC_FULL_SCAN=1  also probe each local IPv4 /24
EOF
}

die() {
	printf '%s\n' "$*" >&2
	exit 1
}

have() {
	command -v "$1" >/dev/null 2>&1
}

ncpus() {
	if have nproc; then
		nproc
	elif have getconf; then
		getconf _NPROCESSORS_ONLN
	else
		printf '%s\n' 2
	fi
}

is_rfc1918() {
	local ip="${1%%/*}" a b
	a="${ip%%.*}"
	b="${ip#*.}"
	b="${b%%.*}"
	[[ ${a} == 10 ]] && return 0
	[[ ${a} == 192 && ${b} == 168 ]] && return 0
	[[ ${a} == 172 && ${b} -ge 16 && ${b} -le 31 ]] && return 0
	return 1
}

load_conf() {
	[[ -f ${CONF} ]] || die "Missing ${CONF}. Run: $0 init"
	# shellcheck disable=SC1090
	source "${CONF}"
	: "${PORT:=3632}"
	: "${LISTEN:=0.0.0.0}"
	: "${ALLOW_PRIVATE:=1}"
	: "${ALLOW:=}"
	: "${JOBS:=0}"
	: "${NICE:=10}"
	: "${JOB_LIFETIME:=3600}"
	: "${LOG_LEVEL:=warning}"
	: "${ZEROCONF:=1}"
	: "${STATS:=0}"
	: "${HOSTS:=localhost/4 +zeroconf}"
	: "${MASQ_PATH:=}"
}

write_conf() {
	local cpus
	cpus="$(ncpus)"
	mkdir -p "${DISTCC_DIR}"
	umask 077
	if [[ ! -f ${CONF} ]]; then
		cat >"${CONF}" <<EOF
# distcc-cluster.conf — sourced by distcc-cluster.sh
PORT=3632
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
		cat >"${HOSTS_FILE}" <<EOF
localhost/${cpus}
+zeroconf
EOF
	fi
	chmod 600 "${CONF}" "${HOSTS_FILE}" 2>/dev/null || true
	printf 'Wrote %s and %s\n' "${CONF}" "${HOSTS_FILE}"
}

find_masq() {
	local d
	if [[ -n ${MASQ_PATH:-} && -d ${MASQ_PATH} ]]; then
		printf '%s\n' "${MASQ_PATH}"
		return
	fi
	for d in \
		/usr/lib/distcc/bin \
		/usr/lib/distcc \
		"${PREFIX:-}/lib/distcc/bin" \
		"${PREFIX:-}/lib/distcc" \
		/data/data/com.termux/files/usr/lib/distcc; do
		if [[ -d ${d} ]]; then
			printf '%s\n' "${d}"
			return
		fi
	done
}

client_exports() {
	load_conf
	local masq jobs
	masq="$(find_masq || true)"
	jobs="$(ncpus)"
	printf 'export DISTCC_DIR=%q\n' "${DISTCC_DIR}"
	printf 'export DISTCC_HOSTS=%q\n' "${HOSTS}"
	printf 'export DISTCC_VERBOSE=%q\n' "${DISTCC_VERBOSE:-0}"
	printf 'export DISTCC_FALLBACK=1\n'
	printf 'export DISTCC_SAVE_TEMPS=0\n'
	if [[ -n ${masq} ]]; then
		printf 'export PATH=%q\n' "${masq}:${PATH}"
	fi
	printf 'export MAKEFLAGS=%q\n' "-j$((jobs * 2))"
}

write_env() {
	client_exports >"${ENV_FILE}"
	chmod 600 "${ENV_FILE}"
	printf 'Wrote %s\n' "${ENV_FILE}"
}

local_ipv4s() {
	if have ip; then
		ip -4 -o addr show scope global | awk '{print $4}' | while read -r cidr; do
			is_rfc1918 "${cidr%%/*}" && printf '%s\n' "${cidr}"
		done
	fi
}

neighbors() {
	if have ip; then
		ip -4 neigh show | awk '/lladdr/ {print $1}' | while read -r ipaddr; do
			is_rfc1918 "${ipaddr}" && printf '%s\n' "${ipaddr}"
		done
	fi
}

subnet_hosts() {
	local cidr="$1" ip mask a b c i
	ip="${cidr%%/*}"
	mask="${cidr##*/}"
	[[ ${mask} == 24 ]] || return 0
	a="${ip%%.*}"
	b="${ip#*.}"
	b="${b%%.*}"
	c="${ip#*.*.}"
	c="${c%%.*}"
	for i in $(seq 1 254); do
		printf '%s.%s.%s.%s\n' "${a}" "${b}" "${c}" "${i}"
	done
}

probe_port() {
	local ip="$1" port="$2"
	if have timeout; then
		timeout 0.2 bash -c "exec 3<>/dev/tcp/${ip}/${port}" >/dev/null 2>&1
	else
		bash -c "exec 3<>/dev/tcp/${ip}/${port}" >/dev/null 2>&1
	fi
}

avahi_distcc() {
	have avahi-browse || return 0
	avahi-browse -artkpt 2>/dev/null | awk -F';' '
		$1=="=" && $3=="IPv4" && $5=="_distcc._tcp" {print $8}
	' | while read -r ipaddr; do
		is_rfc1918 "${ipaddr}" && printf '%s\n' "${ipaddr}"
	done
}

self_ips() {
	if have ip; then
		ip -4 -o addr show | awk '{print $4}' | cut -d/ -f1
	fi
	printf '%s\n' 127.0.0.1
}

discover() {
	load_conf
	mkdir -p "${DISTCC_DIR}"
	local -A skip=() seen=()
	local ip cidr
	while read -r ip; do
		[[ -n ${ip} ]] && skip["${ip}"]=1
	done < <(self_ips)

	{
		neighbors
		avahi_distcc
		if [[ ${DISTCC_FULL_SCAN:-0} == 1 ]]; then
			while read -r cidr; do
				subnet_hosts "${cidr}"
			done < <(local_ipv4s)
		fi
	} | while read -r ip; do
		[[ -n ${ip} && -z ${skip[${ip}]+x} ]] && printf '%s\n' "${ip}"
	done | sort -u >"${DISTCC_DIR}/.probe-candidates"

	: >"${FOUND_FILE}"
	while read -r ip; do
		[[ -z ${ip} ]] && continue
		if probe_port "${ip}" "${PORT}"; then
			printf '%s\n' "${ip}" | tee -a "${FOUND_FILE}"
		fi
	done <"${DISTCC_DIR}/.probe-candidates"
	rm -f "${DISTCC_DIR}/.probe-candidates"
	if [[ ! -s ${FOUND_FILE} ]]; then
		printf 'No distccd listeners on %s (RFC1918 neighbors/mDNS%s).\n' "${PORT}" \
			"$([[ ${DISTCC_FULL_SCAN:-0} == 1 ]] && printf ' + /24' || true)"
		printf 'Start volunteers or rerun with DISTCC_FULL_SCAN=1\n'
	else
		printf 'Wrote %s\n' "${FOUND_FILE}"
	fi
}

ssh_ok() {
	ssh "${SSH_OPTS[@]}" "${SSH_USER}@$1" true >/dev/null 2>&1
}

remote_nproc() {
	ssh "${SSH_OPTS[@]}" "${SSH_USER}@$1" 'nproc 2>/dev/null || echo 4'
}

recruit_one() {
	local host="$1" remote
	have ssh || die 'ssh not in PATH'
	have scp || die 'scp not in PATH'
	[[ -f ${SELF} ]] || die "cannot locate script path: ${SELF}"
	ssh_ok "${host}" || die "SSH BatchMode failed for ${SSH_USER}@${host} (need a key, not a password)"
	remote="/tmp/distcc-cluster.sh"
	scp "${SSH_OPTS[@]}" "${SELF}" "${SSH_USER}@${host}:${remote}"
	ssh "${SSH_OPTS[@]}" "${SSH_USER}@${host}" \
		"test -x \"\$(command -v distccd)\" || { echo distccd-missing; exit 2; }
		 chmod 755 '${remote}'
		 '${remote}' init >/dev/null
		 '${remote}' server-stop >/dev/null 2>&1 || true
		 '${remote}' server-start"
}

merge_hosts() {
	load_conf
	local ip slots line out cpus
	cpus="$(ncpus)"
	out="localhost/${cpus}"
	if [[ -f ${FOUND_FILE} ]]; then
		while read -r ip; do
			[[ -z ${ip} ]] && continue
			slots="$(remote_nproc "${ip}" 2>/dev/null || printf '%s\n' 4)"
			line="${ip}/$((slots + 2)),lzo"
			out="${out} ${line}"
		done <"${FOUND_FILE}"
	fi
	out="${out} +zeroconf"
	HOSTS="${out}"
	if grep -q '^HOSTS=' "${CONF}"; then
		# Replace HOSTS= line only.
		local tmp
		tmp="$(mktemp)"
		awk -v h="${HOSTS}" 'BEGIN{q="\""} /^HOSTS=/{print "HOSTS=" q h q; next} {print}' "${CONF}" >"${tmp}"
		mv -f "${tmp}" "${CONF}"
	fi
	{
		printf 'localhost/%s\n' "${cpus}"
		if [[ -f ${FOUND_FILE} ]]; then
			while read -r ip; do
				[[ -z ${ip} ]] && continue
				slots="$(remote_nproc "${ip}" 2>/dev/null || printf '%s\n' 4)"
				printf '%s/%s,lzo\n' "${ip}" "$((slots + 2))"
			done <"${FOUND_FILE}"
		fi
		printf '+zeroconf\n'
	} >"${HOSTS_FILE}"
	chmod 600 "${CONF}" "${HOSTS_FILE}" 2>/dev/null || true
	printf 'HOSTS=%s\n' "${HOSTS}"
}

recruit_auto() {
	load_conf
	discover
	local ip
	if [[ -f ${FOUND_FILE} ]]; then
		while read -r ip; do
			[[ -z ${ip} ]] && continue
			printf 'already serving: %s:%s\n' "${ip}" "${PORT}"
		done <"${FOUND_FILE}"
	fi
	local cand
	{
		neighbors
		avahi_distcc
		if [[ ${DISTCC_FULL_SCAN:-0} == 1 ]]; then
			while read -r cidr; do
				subnet_hosts "${cidr}"
			done < <(local_ipv4s)
		fi
	} | sort -u | while read -r cand; do
		[[ -z ${cand} ]] && continue
		is_rfc1918 "${cand}" || continue
		if probe_port "${cand}" "${PORT}"; then
			continue
		fi
		if ssh_ok "${cand}"; then
			printf 'recruiting %s@%s\n' "${SSH_USER}" "${cand}"
			if recruit_one "${cand}"; then
				printf '%s\n' "${cand}" >>"${FOUND_FILE}"
			else
				printf 'skip %s (no distccd or start failed)\n' "${cand}"
			fi
		fi
	done
	sort -u -o "${FOUND_FILE}" "${FOUND_FILE}" 2>/dev/null || true
	merge_hosts
	write_env
}

server_start() {
	load_conf
	have distccd || die 'distccd not in PATH'
	if [[ -f ${PID_FILE} ]] && kill -0 "$(cat "${PID_FILE}")" 2>/dev/null; then
		die "distccd already running pid $(cat "${PID_FILE}")"
	fi
	mkdir -p "${DISTCC_DIR}"
	local jobs
	if [[ ${JOBS} -gt 0 ]]; then
		jobs="${JOBS}"
	else
		jobs=$(($(ncpus) + 2))
	fi
	if [[ ${ALLOW_PRIVATE} != 1 && -z ${ALLOW} ]]; then
		die 'Refusing to start: set ALLOW_PRIVATE=1 or ALLOW=CIDR'
	fi
	local argv=(
		distccd
		--daemon
		--port "${PORT}"
		--listen "${LISTEN}"
		--jobs "${jobs}"
		--nice "${NICE}"
		--job-lifetime "${JOB_LIFETIME}"
		--pid-file "${PID_FILE}"
		--log-file "${LOG_FILE}"
		--log-level "${LOG_LEVEL}"
	)
	if [[ ${ALLOW_PRIVATE} == 1 ]]; then
		argv+=(--allow-private)
	fi
	local allow
	# shellcheck disable=SC2086
	for allow in ${ALLOW}; do
		argv+=(--allow "${allow}")
	done
	if [[ ${ZEROCONF} == 1 ]]; then
		argv+=(--zeroconf)
	fi
	if [[ ${STATS} == 1 ]]; then
		argv+=(--stats)
	fi
	"${argv[@]}"
	printf 'distccd started pid %s listen %s:%s jobs %s zeroconf=%s\n' \
		"$(cat "${PID_FILE}")" "${LISTEN}" "${PORT}" "${jobs}" "${ZEROCONF}"
}

server_stop() {
	[[ -f ${PID_FILE} ]] || die "No pid file ${PID_FILE}"
	local pid
	pid="$(cat "${PID_FILE}")"
	kill "${pid}"
	printf 'sent SIGTERM to %s\n' "${pid}"
}

status() {
	load_conf
	if [[ -f ${PID_FILE} ]] && kill -0 "$(cat "${PID_FILE}")" 2>/dev/null; then
		printf 'volunteer: running pid %s\n' "$(cat "${PID_FILE}")"
	else
		printf 'volunteer: not running\n'
	fi
	printf 'DISTCC_DIR=%s\n' "${DISTCC_DIR}"
	printf 'HOSTS=%s\n' "${HOSTS}"
	if [[ -f ${FOUND_FILE} ]]; then
		printf 'discovered:\n'
		cat "${FOUND_FILE}"
	fi
	if have distcc; then
		DISTCC_DIR="${DISTCC_DIR}" DISTCC_HOSTS="${HOSTS}" distcc --show-hosts || true
		DISTCC_DIR="${DISTCC_DIR}" DISTCC_HOSTS="${HOSTS}" distcc -j || true
	fi
}

cmd="${1:-help}"
shift || true
case "${cmd}" in
init) write_conf ;;
server-start) server_start ;;
server-stop) server_stop ;;
client-env) client_exports ;;
write-env) write_env ;;
discover) discover ;;
recruit)
	[[ $# -ge 1 ]] || die 'recruit HOST [HOST...]'
	load_conf
	: >"${FOUND_FILE}"
	for ip in "$@"; do
		recruit_one "${ip}"
		printf '%s\n' "${ip}" >>"${FOUND_FILE}"
	done
	merge_hosts
	write_env
	;;
recruit-auto) recruit_auto ;;
status) status ;;
show-hosts)
	load_conf
	DISTCC_DIR="${DISTCC_DIR}" DISTCC_HOSTS="${HOSTS}" distcc --show-hosts
	;;
help | --help | -h) usage ;;
*)
	usage
	exit 1
	;;
esac
