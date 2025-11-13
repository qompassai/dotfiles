<?php
defined('BASEPATH') OR exit('No direct script access allowed');
/*
 * /qompassai/dotfiles/.config/webapps/filebin/database.php
 * Qompass AI FileBin Database Config
 * Copyright (C) 2025 Qompass AI, All rights reserved
 ****************************************
*/
$active_group = 'default';
$db['default'] = array(
	'dsn'	=> '',
	'hostname' => 'localhost',
	'port'	=> '$(pass show filebin/port)',
	'username' => '$(pass show filebin/user)',
	'password' => '$(pass show filebin/pass)',
	'database' => '$(pass show filebin/db)',
	'dbdriver' => 'mysqli',
	'dbprefix' => '',
	'pconnect' => FALSE,
	'db_debug' => TRUE,
	'char_set' => 'utf8',
	'dbcollat' => 'utf8_bin',
	'swap_pre' => '',
	'encrypt' => TRUE,
	'compress' => FALSE,
	'stricton' => TRUE,
	'failover' => array(),
	'save_queries' => TRUE
);
if (getenv("ENVIRONMENT") === "testsuite") {
	$db['default']['database'] = "filebin_testsuite";
	$db['default']['dbprefix'] = "testsuite_prefix_";
}
?>
