# /qompassai/dotfiles/.config/siteconfig/siteconfig.tcl
# Qompass AI SiteConfig Config
# Copyright (C) 2025 Qompass AI, All rights reserved
#################################################
site-specific configuration script
lappendConf locked_configs extra_siteconfig
lappendConf locked_configs implicit_default
lappendConf locked_configs logged_events logger
set modulefile_extra_vars {varname1 value1 varname2 value2}
set modulefile_extra_cmds {command1 procedure1 command2 procedure2}
set modulerc_extra_vars {varname1 value1 varname2 value2}
set modulerc_extra_cmds {command1 procedure1 command2 procedure2}
