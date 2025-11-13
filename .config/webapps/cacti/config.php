<?php
/*
* /qompassai/dotfiles/.config/webapps/cacti/config.php
* Qompass AI Cacti Config
* Copyright (C) 2025 Qompass AI, All rights reserved
******************************************************
*/
$cacti_cookie_domain   = '$(pass show cacti/cookie_domain)';
$cacti_db_session      = true;
$cacti_session_name    = '$(pass show cacti/sessionname)';
$database_default     = '$(pass show cacti/dbdefault)';
$database_hostname    = '$(pass show cacti/hostname)';
$database_password    = '$(pass show cacti/dbpass)';
$database_port        = '$(pass show cacti/dbport)';
$database_retries     = 5;
$database_ssl         = true;
$database_ssl_ca      = '/etc/ssl/certs/ca-certificates.crt';
$database_ssl_cert    = $XDG_DATA_HOME . '/webapps/cacti/db-client.key';
$database_ssl_key     = $XDG_DATA_HOME . '/webapps/cacti/db-client.key';
$database_type        = '$(pass show cacti/dbtype)';
$database_username    = '$(pass show cacti/dbuser)';
$database_persist     = true;
$disable_log_rotation  = false;
$i18n_force_language   = 'en_US';
$i18n_handler          = 'gettext';
$i18n_log              = true;
$i18n_text_log         = true;
$input_whitelist       = $CACTI_CONFIG_DIR . "/input_whitelist.jsonc";
$rdatabase_default    = 'cacti';
$rdatabase_hostname   = 'localhost';
$rdatabase_password   = '$(pass show cacti/rdbpass)';
$rdatabase_port       = '$(pass show cacti/rdbport)';
$rdatabase_retries    = 5;
$rdatabase_ssl        = true;
$rdatabase_ssl_ca     = '/etc/ssl/certs/ca-certificates.crt';
$rdatabase_ssl_cert   = $XDG_DATA_HOME . '/webapps/cacti/rdb-client.crt';
$rdatabase_ssl_key    = $XDG_DATA_HOME . '/webapps/cacti/rdb-client.key';
$rdatabase_type       = '$(pass show cacti/rdbtype)';
$rdatabase_username   = '$(pass show cacti/rdbuser)';
$proxy_headers = array('X-Forwarded-For', 'X-Real-IP');
$path_csrf_secret      = $CACTI_SHARE_DIR . "/resource/csrf-secret.php";
$php_path              = '/usr/bin/php';
$php_snmp_support      = true;
$poller_id             = 1;
$resource_path         = $CACTI_SHARE_DIR . "/resource/";
$scripts_path          = $CACTI_SHARE_DIR . "/scripts/";
$url_path              = '/cacti/';
if (!defined('DEBUG_READ_CONFIG_OPTION')) {
    define('DEBUG_READ_CONFIG_OPTION', true);
}
if (!defined('DEBUG_READ_CONFIG_OPTION_DB_OPEN')) {
    define('DEBUG_READ_CONFIG_OPTION_DB_OPEN', true);
}
if (!defined('DEBUG_SQL_CMD')) {
    define('DEBUG_SQL_CMD', true);
}
if (!defined('DEBUG_SQL_CONNECT')) {
    define('DEBUG_SQL_CONNECT', true);
}
if (!defined('DEBUG_SQL_FLOW')) {
    define('DEBUG_SQL_FLOW', true);
}
?>
