<?php
/*
 * /qompassai/dotfiles/.config/webapps/pydio/bootstrap_conf.php
 * Qompass AI Pydio BootStrap Config
 * Copyright (C) 2025 Qompass AI, All rights reserved
 ****************************************
 */
define("AJXP_LOCALE", "en_EN.UTF-8");
$config_home = getenv("XDG_CONFIG_HOME") ?: getenv("HOME") . "/.config";
$data_home = getenv("XDG_DATA_HOME") ?: getenv("HOME") . "/.local/share";
$tmp_dir = $data_home . "/pydio/tmp";
$sessions_dir = $tmp_dir . "/sessions";
define("AJXP_TMP_DIR", $tmp_dir);
$AJXP_INISET = array();
$AJXP_INISET["session.save_path"] = $sessions_dir;
$AJXP_INISET["session.cookie_path"] = "/ajaxplorer";
define("AJXP_FORCE_SSL_REDIRECT", true);
?>
