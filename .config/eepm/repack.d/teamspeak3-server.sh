#!/bin/sh -x

# It will be run with two args: buildroot spec
BUILDROOT="$1"
SPEC="$2"

. $(dirname $0)/common.sh

# Move to /opt/teamspeak3-server
move_to_opt

add_bin_link_command ts3server $PRODUCTDIR/ts3server

# Create systemd service
cat <<EOF | create_file /usr/lib/systemd/system/teamspeak3-server.service
[Unit]
Description=TeamSpeak3 Server
After=network.target

[Service]
Type=forking
User=teamspeak
Group=teamspeak
WorkingDirectory=/opt/teamspeak3-server
ExecStart=/opt/teamspeak3-server/ts3server inifile=/etc/teamspeak3-server/ts3server.ini
ExecStop=/usr/bin/kill \$MAINPID
PIDFile=/var/run/teamspeak3-server/ts3server.pid
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

# Create tmpfiles.d for directories
cat <<EOF | create_file /usr/lib/tmpfiles.d/teamspeak3-server.conf
d /var/run/teamspeak3-server 0755 teamspeak teamspeak -
d /var/lib/teamspeak3-server 0755 teamspeak teamspeak -
d /var/log/teamspeak3-server 0755 teamspeak teamspeak -
EOF

# Create config directory
mkdir -p $BUILDROOT/etc/teamspeak3-server

# Create default config
cat <<EOF | create_file /etc/teamspeak3-server/ts3server.ini
machine_id=
default_voice_port=9987
voice_ip=0.0.0.0
licensepath=/var/lib/teamspeak3-server/
filetransfer_port=30033
filetransfer_ip=0.0.0.0
query_port=10011
query_ip=0.0.0.0
dbplugin=ts3db_sqlite3
dbpluginparameter=
dbsqlpath=/opt/teamspeak3-server/sql/
dbsqlcreatepath=create_sqlite/
logpath=/var/log/teamspeak3-server/
logquerycommands=0
dbclientkeepdays=30
logappend=0
EOF

# Set PRODUCT to add user
cat <<EOF | create_file /etc/sysusers.d/teamspeak.conf
u teamspeak - "TeamSpeak3 Server" /var/lib/teamspeak3-server
EOF
