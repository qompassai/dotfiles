#!/bin/sh

TAR="$1"
RETURNTARNAME="$2"
VERSION="$3"

. $(dirname $0)/common.sh

[ -n "$VERSION" ] || VERSION="0"

PKGNAME=$PRODUCT-$VERSION

# Install JAR
install -D -m644 "$TAR" usr/share/java/$PRODUCT.jar || fatal

# Create launcher script
cat <<'EOF' | create_file usr/bin/$PRODUCT
#!/bin/sh
exec /usr/bin/java -Dfile.encoding=UTF-8 -jar -Xmx512m /usr/share/java/stirling-pdf.jar "$@"
EOF
chmod 755 usr/bin/$PRODUCT

# Create systemd service
cat <<'EOF' | create_file usr/lib/systemd/system/$PRODUCT.service
[Unit]
Description=Stirling-PDF Service
Documentation=https://docs.stirlingpdf.com
Wants=network-online.target
After=network-online.target

[Service]
User=stirling-pdf
Group=stirling-pdf
Restart=on-failure
WorkingDirectory=/var/lib/stirling-pdf
EnvironmentFile=-/etc/stirling-pdf/stirling-pdf.env
ExecStart=/usr/bin/stirling-pdf
KillMode=control-group
TimeoutStopSec=10
SuccessExitStatus=0 143
RestartForceExitStatus=0 143

[Install]
WantedBy=multi-user.target
EOF

# Create default config
cat <<'EOF' | create_file etc/$PRODUCT/$PRODUCT.env
# Stirling-PDF configuration
# See https://docs.stirlingpdf.com/Configuration/System%20and%20Security

# Listen address
SERVER_HOST=127.0.0.1

# Listen port
SERVER_PORT=8080

# Enable login (set to true to require authentication)
SECURITY_ENABLELOGIN=false
EOF

# Create sysusers.d config for user creation
cat <<EOF | create_file usr/lib/sysusers.d/$PRODUCT.conf
u stirling-pdf - "Stirling-PDF service" /var/lib/stirling-pdf
EOF

# Create tmpfiles.d config for directories
cat <<EOF | create_file usr/lib/tmpfiles.d/$PRODUCT.conf
d /var/lib/stirling-pdf 0750 stirling-pdf stirling-pdf -
EOF

erc pack $PKGNAME.tar usr etc

cat <<EOF >$PKGNAME.tar.eepm.yaml
name: $PRODUCT
version: $VERSION
group: Publishing
license: MIT
url: https://stirlingpdf.io/
summary: Web application for PDF operations
description: Locally hosted web application for PDF operations (merge, split, convert, OCR, compress).
requires: java-21-openjdk-headless
EOF

return_tar $PKGNAME.tar
