#!/bin/sh -x
# It will be run with two args: buildroot spec
BUILDROOT="$1"
SPEC="$2"
PRODUCT=spo-anketa
PRODUCTDIR=/opt/$PRODUCT

. $(dirname $0)/common.sh

# Move from Russian name to ASCII
move_to_opt "/opt/Анкета ГС (МС)"

# Install icon
install_file $PRODUCTDIR/resources/bin/Assets/256x256.png /usr/share/icons/hicolor/256x256/apps/$PRODUCT.png

# Create binary link for command line execution
add_bin_link_command $PRODUCT $PRODUCTDIR/spo-anketa

add_electron_deps

# Remove original desktop file
remove_file /usr/share/applications/spo-anketa.desktop

# Create proper desktop file
cat <<EOF | create_file /usr/share/applications/$PRODUCT.desktop
[Desktop Entry]
Version=1.0
Type=Application
Name=Анкета ГС (МС)
Comment=СПО для заполнения анкеты госслужащего
Icon=$PRODUCT
Exec=$PRODUCT %U
Categories=Office;
Terminal=false
StartupWMClass=$PRODUCT
EOF
