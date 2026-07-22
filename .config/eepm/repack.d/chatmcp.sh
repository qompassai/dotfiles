#!/bin/sh -x

# It will be run with two args: buildroot spec
BUILDROOT="$1"
SPEC="$2"

PRODUCT=chatmcp

. $(dirname $0)/common.sh

move_to_opt /usr/share/$PRODUCT

add_bin_link_command $PRODUCT
