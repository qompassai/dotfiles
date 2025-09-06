<!-- README.md -->
<!-- Qompass AI - [Add description here] -->
<!-- Copyright (C) 2025 Qompass AI, All rights reserved -->
<!-- ---------------------------------------- -->

# cgconfig.conf

# SPDX-License-Identifier: LGPL-2.1-only
#
#  Copyright IBM Corporation. 2007
#
#  Authors:	Balbir Singh <balbir@linux.vnet.ibm.com>
#
#group daemons/www {
#	perm {
#		task {
#			uid = root;
#			gid = webmaster;
#		}
#		admin {
#			uid = root;
#			gid = root;
#		}
#	}
#	cpu {
#		cpu.shares = 1000;
#	}
#}
#
#group daemons/ftp {
#	perm {
#		task {
#			uid = root;
#			gid = ftpmaster;
#		}
#		admin {
#			uid = root;
#			gid = root;
#		}
#	}
#	cpu {
#		cpu.shares = 500;
#	}
#}
#
#mount {
#	cpu = /sys/fs/cgroup/cpu;
#	cpuacct = /sys/fs/cgroup/cpuacct;
#}

# cgrules.conf
# /etc/cgrules.conf
#The format of this file is described in cgrules.conf(5)
#manual page.
#
# Example:
#<user>		<controllers>	<destination>
#@student	cpu,memory	usergroup/student/
#peter		cpu		test1/
#%		memory		test2/
# End of file

# cgsnapshot_allowlist.conf

# cgsnapshot_denylist.conf
