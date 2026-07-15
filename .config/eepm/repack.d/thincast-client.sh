#!/bin/sh -x

# It will be run with two args: buildroot spec
BUILDROOT="$1"
SPEC="$2"

PRODUCT=thincast-client
PRODUCTDIR=/opt/$PRODUCT

. $(dirname $0)/common.sh

# Remove bundled PulseAudio libs - use system ones (avoids AppArmor dependency)
remove_file $PRODUCTDIR/usr/lib/x86_64-linux-gnu/libpulse.so.0
remove_file $PRODUCTDIR/usr/lib/x86_64-linux-gnu/libpulse.so.0.24.1
remove_file $PRODUCTDIR/usr/lib/x86_64-linux-gnu/libpulse-simple.so.0
remove_file $PRODUCTDIR/usr/lib/x86_64-linux-gnu/libpulse-simple.so.0.1.1
remove_dir $PRODUCTDIR/usr/lib/x86_64-linux-gnu/pulseaudio

# Ignore bundled libraries dependencies (ICU 70, etc.)
ignore_lib_requires libbz2 libedit libicudata libicui18n libicuio libicutest libicutu libicuuc

# Override wrapper scripts to set LD_LIBRARY_PATH for bundled libs
LIBDIRS="$PRODUCTDIR/lib:$PRODUCTDIR/lib/x86_64-linux-gnu:$PRODUCTDIR/usr/lib:$PRODUCTDIR/usr/lib/x86_64-linux-gnu:$PRODUCTDIR/usr/lib/x86_64-linux-gnu/freerdp3"

cat <<EOF | create_exec_file "/usr/bin/rdc"
#!/bin/sh
export LD_LIBRARY_PATH="$LIBDIRS:\$LD_LIBRARY_PATH"
exec "$PRODUCTDIR/usr/bin/rdc" "\$@"
EOF

cat <<EOF | create_exec_file "/usr/bin/rdwebaccessclient"
#!/bin/sh
export LD_LIBRARY_PATH="$LIBDIRS:\$LD_LIBRARY_PATH"
exec "$PRODUCTDIR/usr/bin/rdwebaccessclient" "\$@"
EOF
