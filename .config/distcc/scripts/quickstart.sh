#!/usr/bin/env bash
# #################################################################
# /qompassai/.config/distcc/scripts/quickstart.sh
# Qompass AI Quickstart
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
# Then edit $DISTCC_DIR/cluster.conf HOSTS= and start a volunteer:
#   ./distcc-cluster.sh server-start
# On a client:
#   eval "$(./distcc-cluster.sh client-env)"
#   make -j"$(distcc -j)"
#
# TCP distccd is unauthenticated remote code execution for anyone who
# can connect. This kit never passes --enable-tcp-insecure, never
# advertises via zeroconf by default, and requires --allow-private
# and/or explicit CIDR. Do not forward port 3632 to the internet.
# SSH volunteers (@host) do not run a daemon; distccd is started by ssh.
#
# CLI reference: distcc / distccd 3.4
# https://github.com/distcc/distcc

set -eu
set -o pipefail

DISTCC_DIR="${DISTCC_DIR:-${HOME}/.distcc}"
CONF="${DISTCC_DIR}/cluster.conf"
HOSTS_FILE="${DISTCC_DIR}/hosts"
PID_FILE="${DISTCC_DIR}/distccd.pid"
LOG_FILE="${DISTCC_DIR}/distccd.log"
ENV_FILE="${DISTCC_DIR}/client.env"

usage() {
	cat <<'EOF'
Usage: distcc-cluster.sh <command>

  init            Create DISTCC_DIR, cluster.conf, and hosts (no overwrite of conf)
  server-start    Start distccd as this machine's volunteer
  server-stop     SIGTERM the volunteer recorded in the pid file
  client-env      Print export lines (eval "$(... client-env)")
  write-env       Write the same exports to $DISTCC_DIR/client.env
  status          Show pid, port, hosts, and distcc -j
  show-hosts      distcc --show-hosts
  help            This text

Environment: DISTCC_DIR (default ~/.distcc)
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
	: "${ZEROCONF:=0}"
	: "${STATS:=0}"
	: "${HOSTS:=localhost/4}"
	: "${MASQ_PATH:=}"
}

write_conf() {
	local cpus jobs
	cpus="$(ncpus)"
	jobs=$((cpus + 2))
	mkdir -p "${DISTCC_DIR}"
	umask 077
	if [[ ! -f ${CONF} ]]; then
		cat >"${CONF}" <<EOF
# distcc-cluster.conf — sourced by distcc-cluster.sh
# Same file on every node. Edit HOSTS on clients; volunteers use the server keys.

PORT=3632
LISTEN=0.0.0.0
ALLOW_PRIVATE=1
# Extra CIDR or addresses, space-separated. Example: ALLOW="2001:db8:1::/64"
ALLOW=""
# 0 = nproc+2 (distccd default policy)
JOBS=0
NICE=10
JOB_LIFETIME=3600
LOG_LEVEL=warning
ZEROCONF=0
STATS=0

# Client host list, most capable volunteer first.
# Forms: localhost/N   HOST/N   HOST:PORT/N   USER@HOST/N
# Suffixes: ,lzo  ,cpp,lzo (pump)  ,auth
# SSH (@host) does not need distccd running on the volunteer.
HOSTS="localhost/${cpus}"

# Optional masquerade dir prepended to PATH on clients.
# Arch: /usr/lib/distcc/bin   Debian: /usr/lib/distcc
MASQ_PATH=""
EOF
	fi
	if [[ ! -f ${HOSTS_FILE} ]]; then
		cat >"${HOSTS_FILE}" <<EOF
# $HOSTS_FILE — used if DISTCC_HOSTS is unset
# Ordered most powerful first. localhost is for link + fallback.
localhost/${cpus}
# 192.168.1.10/${jobs},lzo
# 192.168.1.11/8,lzo
# @otherbox/4,lzo
EOF
	fi
	chmod 600 "${CONF}" "${HOSTS_FILE}" 2>/dev/null || true
	printf 'Wrote %s and %s\n' "${CONF}" "${HOSTS_FILE}"
}

find_masq() {
	local d
	if [[ -n ${MASQ_PATH} && -d ${MASQ_PATH} ]]; then
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

server_argv() {
	load_conf
	have distccd || die 'distccd not in PATH'
	local jobs argv allow
	if [[ ${JOBS} -gt 0 ]]; then
		jobs="${JOBS}"
	else
		jobs=$(($(ncpus) + 2))
	fi
	argv=(
		distccd
		--daemon
		--no-detach
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
	# shellcheck disable=SC2086
	for allow in ${ALLOW}; do
		argv+=(--allow "${allow}")
	done
	if [[ ${ALLOW_PRIVATE} != 1 && -z ${ALLOW} ]]; then
		die 'Refusing to start: set ALLOW_PRIVATE=1 or ALLOW=CIDR (distccd exits with no --allow)'
	fi
	if [[ ${ZEROCONF} == 1 ]]; then
		argv+=(--zeroconf)
	fi
	if [[ ${STATS} == 1 ]]; then
		argv+=(--stats)
	fi
	printf '%s\n' "${argv[@]}"
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
	# Never: --enable-tcp-insecure, --inetd, --wizard, --no-fork
	"${argv[@]}"
	printf 'distccd started pid %s listen %s:%s jobs %s\n' "$(cat "${PID_FILE}")" "${LISTEN}" "${PORT}" "${jobs}"
	printf 'log %s\n' "${LOG_FILE}"
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
	if have distcc; then
		DISTCC_DIR="${DISTCC_DIR}" DISTCC_HOSTS="${HOSTS}" distcc --show-hosts || true
		DISTCC_DIR="${DISTCC_DIR}" DISTCC_HOSTS="${HOSTS}" distcc -j || true
	fi
}

cmd="${1:-help}"
case "${cmd}" in
init) write_conf ;;
server-start) server_start ;;
server-stop) server_stop ;;
client-env) client_exports ;;
write-env) write_env ;;
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
