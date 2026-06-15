#!/bin/sh -x
# It will run with two args: buildroot spec
BUILDROOT="$1"
SPEC="$2"

PKGNAME=obs-studio-plugin-distroav

. $(dirname $0)/common.sh

# rename package from distroav to obs-studio-plugin-distroav
subst "s|^Name:.*|Name: $PKGNAME|" $SPEC

# add dependency on obs-studio
add_requires obs-studio
