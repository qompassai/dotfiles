<!-- README.md -->
<!-- Qompass AI - [Add description here] -->
<!-- Copyright (C) 2025 Qompass AI, All rights reserved -->
<!-- ---------------------------------------- -->
#
# Configuration file for Herald.
#

# XMPP server to connect to.
server = "xmpp.example.com"

# XMPP username, including domain name.
username = "user@example.com"

# XMPP password
password = "verysecret"

# The security of the XMPP connection can be set to:
#  none -- No encryption
#  tls -- SSL/TLS
#  starttls -- In-band STARTTLS (default)
#security = "starttls"

# Recipients who should receive the messages.
recipients = [
    "admin@example.com",
]

# Message format in Go templates syntax.
# The template is executed with the Journal message as data.
# See systemd.journal-fields(7) for the list of fields.
# Default format is "{{._COMM}}: {{.MESSAGE}}".
#format = "{{._COMM}}: {{.MESSAGE}}"

# Matchers.
# Each match entry consists of a list of criteria that should all be satisfied.
# Match prefixes:
# = : exact match (prefix may be omitted)
# ! : inverse match
# ~ : regular expression
# >, < : arithmetic inequality
#
# Value may be either a single string or an array of strings

[[match]]  # Messages with priority warning and above
PRIORITY = '<5'

[[match]]  # SSH logins
_COMM = 'sshd'
MESSAGE = '~^Accepted'
