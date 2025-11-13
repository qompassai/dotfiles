<?php
/*
 * /qompassai/dotfiles/.config/webapps/filebin/memcached.php
 * Qompass AI FileBin MemCached Config
 * Copyright (C) 2025 Qompass AI, All rights reserved
 ****************************************
*/
$act
$config = array(
	"default" => array(
		"hostname" => "127.0.0.1",
		"port" => '$(pass show filebin/port)',
		"weight" => 1,
	),
	"socket" => array(
		"hostname" => FCPATH.'/memcached.sock',
		"port" => 0,
		"weight" => 2,
	),
);
?>
