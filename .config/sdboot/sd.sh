#!/usr/bin/env sh
if [ -f /etc/nixos ]; then
    ENTRY_ROOT="/nix/var/nix/profiles/system"
elif [ -f /etc/arch-release ]; then
    ENTRY_ROOT="/boot/loader/entries"
else
    ENTRY_ROOT="/boot/loader/entries"
fi
cat > sdboot-manage.conf <<EOF
DEFAULT_ENTRY="latest"
ENTRY_ROOT="$ENTRY_ROOT"
REMOVE_EXISTING="no"
OVERWRITE_EXISTING="no"
REMOVE_OBSOLETE="yes"
PRESERVE_FOREIGN="yes"
NO_AUTOGEN="yes"
NO_AUTOUPDATE="no"
LINUX_OPTIONS="root=PARTUUID=714c9eee-4984-4113-bfbd-ffb9b74f3e3e rw rootflags=subvol=@ quiet splash zswap.enabled=0 nvidia_drm.modeset=1 i915.force_probe=a7a8 xe.force_probe=a7a8 xe.enable_guc=3 xe.enable_psr=1 xe.enable_fbc=1 xe.fastboot=1 mitigations=off ibt=off i915.enable_hangcheck=0"
EOF
