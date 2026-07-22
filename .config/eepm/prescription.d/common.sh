#!/bin/sh

# kind of hack: inheritance --force from main epm
echo "$EPM_OPTIONS" | grep -q -- "--force" && force="--force"
echo "$EPM_OPTIONS" | grep -q -- "--auto" && auto="--auto"
echo "$EPM_OPTIONS" | grep -q -- "--verbose" && verbose="--verbose"

fatal()
{
    echo "FATAL: $*" >&2
    exit 1
}

info()
{
    echo "$*" >&2
}

is_root()
{
	local EFFUID="$(id -u)"
	[ "$EFFUID" = "0" ]
}

assure_root()
{
	is_root || fatal "run me only under root"
}


# detect bash
is_bash()
{
    [ -n "$BASH_VERSION" ]
}

# print a path to the command if exists in $PATH
if is_bash ; then
print_command_path()
{
    type -fpP -- "$1" 2>/dev/null
}
else
print_command_path()
{
    command -v "$1" 2>/dev/null
}
fi

# check if <arg> is a real command
is_command()
{
    print_command_path "$1" >/dev/null
}

# add to all epm calls
#EPM="$(epm tool which epm)" || fatal
EPM="$(print_command_path epm)" || fatal
epm()
{
    #if [ "$1" = "tool" ] ; then
    #    __showcmd_shifted 1 "$@"
    if [ "$1" != "print" ] && [ "$1" != "tool" ] && [ "$1" != "status" ] ; then
        showcmd "$(basename $EPM) $*"
    fi
    $EPM "$@"
}

. $(dirname $0)/common-outformat.sh

check_tty

if [ -n "$DESCRIPTION" ] ; then
    [ "$1" != "--run" ] && echo "$DESCRIPTION" && exit
fi
