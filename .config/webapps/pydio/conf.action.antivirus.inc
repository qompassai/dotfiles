<?php
/*
 * /qompassai/dotfiles/.config/webapps/pydio/conf.access.smb.inc
 * Qompass AI Pydio SMB Access Config
 * Copyright (C) 2025 Qompass AI, All rights reserved
 ****************************************
 */
defined('AJXP_EXEC') or die('Access not allowed');
$DRIVER_CONF = [
    "COMMAND" => "/usr/bin/clamscan --remove=yes \$FILE"
];
