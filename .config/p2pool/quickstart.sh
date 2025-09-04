#!/usr/bin/env sh
# quickstart.sh
# Qompass AI P2Pool Quickstart
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
p2pool \
	--wallet 48YUZsTn4MJ6JQDZDW4Stq1BRhqGuwrUrKpBMhgqWuZv99qXLYMRseCFjjEMQgGmmLDagv7MFL92iPcL6sZSxBXuQmonmvH \
	--host 127.0.0.1 \
	--rpc-port 18081 \
	--zmq-port 18083 \
	--stratum [::]:3333 \
	--p2p [::]:37889 \
	--data-dir /home/phaedrus/.local/share/p2pool \
	--loglevel 3
