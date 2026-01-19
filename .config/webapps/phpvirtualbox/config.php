<?php
/*
* /qompassai/dotfiles/.config/webapps/phppgadmin/config.php
* Qompass AI PHP VirtualBox Config
* Copyright (C) 2025 Qompass AI, All rights reserved
****************************************************
 */
class phpVBoxConfig {
var $username = 'vbox';
var $password = 'pass';
var $location = 'http://127.0.0.1:18083/';
var $language = 'en';
var $vrdeports = '9000-9100';
var $vrdeaddress = '192.168.1.1';
var $servers = array(
        array(
                'name' => 'London',
                'username' => '$(pass show phpvbox/user)',
                'password' => '$(pass show phpvbox/pass)',
                'location' => 'http://192.168.1.1:18083/',
                'authMaster' => true 
        ),
        array(
                'name' => 'New York',
                'username' => '$(pass show phpvbox/user2)',
                'password' => '$(psas show phpvbox/pass2)',
                'location' => 'http://192.168.1.2:18083/'
        ),
);
*/
var $noAuth = true;
var $consoleHost = '$(pass show phpvbox/chost)';
var $noPreview = true;
var $previewUpdateInterval = 30;
var $previewWidth = 180;
var $maxProgressList = 5;
var $previewAspectRatio = 1.6;
var $enableCustomIcons = true;
var $phpVboxGroups = true;
var $deleteOnRemove = true;
var $browserRestrictFiles = array('.iso','.vdi','.vmdk','.img','.bin','.vhd','.hdd','.ovf','.ova','.xml','.vbox','.cdr','.dmg','.ima','.dsk','.vfd');
#var $browserRestrictFolders = array('D:\\','C:\\Users\\$USER');
var $browserLocal = true;
var $browserDisable = true;
var $noWindowsDriveList = true;
var $forceWindowsAllDriveList = true;
var $hostMemInfoRefreshInterval = 5;
var $hostMemInfoShowFreePct = true;
var $vmMemoryStartLimitWarn = true;
var $vmMemoryOffset = 100;
var $enableGuestAdditionsVersionDisplay = true;
var $disableTabVMSnapshots = true;
var $disableTabVMConsole = true;
var $consoleResolutions = array('640x480','800x600','1024x768','1280x720','1440x900');
var $consoleKeyboardLayout = 'EN';
var $nicMax = 4;
var $enableAdvancedConfig = true;
var $startStopConfig = true;
 var $authLib = 'Builtin';
var $enforceVMOwnership = true;
var $vmQuotaPerUser = 2;
var $enableVDE = true; 
var $disableSataPortCount = true;
var $enableLPTConfig = true;
var $enableHDFlushConfig = true;
var $eventListenerTimeout = 20;
}
?>
