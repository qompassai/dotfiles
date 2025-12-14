<?php
/*
* /qompassai/dotfiles/.config/webapps/pydio/bootstrap_context.php
* Qompass AI Pydio BootStrap Context Config
* Copyright (C) 2025 Qompass AI, All rights reserved
**************************************************************
*/
@date_default_timezone_set(@date_default_timezone_get());
if (function_exists("xdebug_disable")) {
    xdebug_disable();
}
@error_reporting(E_ALL & ~E_NOTICE & ~E_STRICT);
@libxml_disable_entity_loader(false);
$HOME = getenv("HOME");
$XDG_CONFIG_HOME = getenv("XDG_CONFIG_HOME") ?: $HOME . "/.config";
$XDG_DATA_HOME = getenv("XDG_DATA_HOME") ?: $HOME . "/.local/share";
$XDG_CACHE_HOME = getenv("XDG_CACHE_HOME") ?: $HOME . "/.cache";
$XDG_LOG_HOME = getenv("XDG_STATE_HOME") ?: $HOME . "/.local/state";
$INSTALL_PATH = $XDG_CONFIG_HOME . "/webapps/pydio";
$CONF_PATH = $INSTALL_PATH;
$DATA_PATH = $XDG_DATA_HOME . "/pydio";
$CACHE_DIR = $XDG_CACHE_HOME . "/pydio";
$LOG_DIR = $XDG_LOG_HOME . "/pydio";
@include_once("VERSION.php");
if(!defined("AJXP_VERSION")){
    list($vNmber,$vDate,$vRevision,$vDbVersion) = explode("__",file_get_contents($CONF_PATH."/VERSION"));
    define("AJXP_VERSION", $vNmber);
    define("AJXP_VERSION_DATE", $vDate);
    if(!empty($vRevision)) define("AJXP_VERSION_REV", $vRevision);
    if(!empty($vDbVersion)) define("AJXP_VERSION_DB", intval($vDbVersion));
}
define("ADMIN_PASSWORD", "$(pass show pydio/adminp)");
define("AJXP_BIN_FOLDER", $INSTALL_PATH . "/core/src");
define("AJXP_BIN_FOLDER_REL", "core/src");
define("AJXP_CACHE_DIR", $CACHE_DIR);
define("AJXP_CLIENT_DEBUG", false);
define("AJXP_CONF_PATH", $CONF_PATH);
define("AJXP_COREI18N_FOLDER", $INSTALL_PATH . "/plugins/core.ajaxplorer/i18n");
define("AJXP_DATA_PATH", $DATA_PATH);
define("AJXP_DOCS_FOLDER", "core/doc");
define("AJXP_EXEC", true);
define("AJXP_FORCED_LOGPATH", $LOG_DIR);
define("AJXP_INSTALL_PATH", $INSTALL_PATH);
define("AJXP_PLUGINS_BOOTSTRAP_CACHE", $CACHE_DIR . "/plugins_bootstrap.php");
define("AJXP_PLUGINS_CACHE_FILE", $CACHE_DIR . "/plugins_cache.ser");
define("AJXP_PLUGINS_FOLDER", "plugins");
define("AJXP_PLUGINS_MESSAGES_FILE", $CACHE_DIR . "/plugins_messages.ser");
define("AJXP_PLUGINS_QUERIES_CACHE", $CACHE_DIR . "/plugins_queries.ser");
define("AJXP_PLUGINS_REPOSITORIES_CACHE", $CACHE_DIR . "/plugins_repositories.php");
define("AJXP_PLUGINS_REQUIRES_FILE", $CACHE_DIR . "/plugins_requires.ser");
define("AJXP_SERVER_ACCESS", "index.php");
define("AJXP_SERVER_DEBUG", false);
define("AJXP_SHARED_CACHE_DIR", $CACHE_DIR);
define("AJXP_SKIP_CACHE", false);
define("AJXP_TESTS_FOLDER", $INSTALL_PATH . "/core/src/pydio/Tests");
define("AJXP_VENDOR_FOLDER", $INSTALL_PATH . "/core/vendor");
define("AJXP_VENDOR_FOLDER_REL", "core/vendor");
define("INITIAL_ADMIN_PASSWORD", "$(pass show pydio/adminipass)");
define("PBKDF2_HASH_ALGORITHM", "sha256");
define("PBKDF2_HASH_BYTE_SIZE", 24);
define("PBKDF2_ITERATIONS", 1000);
define("PBKDF2_SALT_BYTE_SIZE", 24);
define("PYDIO_BOOSTER_TASK_IDENTIFIER", "pydio-booster");
define("TESTS_RESULT_FILE", $DATA_PATH . "/plugins/boot.conf/diag_result.php");
define("TESTS_RESULT_FILE_LEGACY", $CACHE_DIR . "/diag_result.php");
define("USE_OPENSSL_RANDOM", true);
define("HASH_ALGORITHM_INDEX", 0);
define("HASH_ITERATION_INDEX", 1);
define("HASH_PBKDF2_INDEX", 3);
define("HASH_SALT_INDEX", 2);
define("HASH_SECTIONS", 4);
define("AJXP_LOCALE", "en_EN.UTF-8");
require_once (AJXP_VENDOR_FOLDER . "/autoload.php");
$corePlugAutoloads = glob($INSTALL_PATH . "/" . AJXP_PLUGINS_FOLDER . "/core.*/vendor/autoload.php", GLOB_NOSORT);
if ($corePlugAutoloads !== false && count($corePlugAutoloads)) {
    foreach($corePlugAutoloads as $autoloader){
        require_once($autoloader);
    }
}
function pydioAutoloader($className)
{
    $parts = explode("\\", $className);
    $className = array_pop($parts);
    if($className == "dibi"){
        require_once(AJXP_BIN_FOLDER . "/lib/dibi/dibi.php");
    }
    $corePlugClass = glob($INSTALL_PATH . "/" . AJXP_PLUGINS_FOLDER . "/core.*/" . $className . ".php", GLOB_NOSORT);
    if ($corePlugClass !== false && count($corePlugClass)) {
        require_once($corePlugClass[0]);
        return;
    }
}
spl_autoload_register('pydioAutoloader');
include_once($INSTALL_PATH . "/core/compat.php");
use Pydio\Core\Services\ApplicationState;
ApplicationState::safeIniSet("session.cookie_httponly", 1);
if (is_file($CONF_PATH . "/bootstrap_conf.php")) {
    include($CONF_PATH . "/bootstrap_conf.php");
    if (isset($AJXP_INISET)) {
        foreach($AJXP_INISET as $key => $value) ApplicationState::safeIniSet($key, $value);
    }
    if (defined('AJXP_LOCALE')) {
        setlocale(LC_CTYPE, AJXP_LOCALE);
    } else if (file_exists($DATA_PATH . "/plugins/boot.conf/encoding.php")) {
        require_once($DATA_PATH . "/plugins/boot.conf/encoding.php");
        if (isset($ROOT_ENCODING)) {
            setlocale(LC_CTYPE, $ROOT_ENCODING);
        }
    }
}
if (!is_file(AJXP_PLUGINS_BOOTSTRAP_CACHE)){
    $content = "<?php \n";
    $boots = glob($INSTALL_PATH . "/" . AJXP_PLUGINS_FOLDER . "/*/bootstrap.php");
    if ($boots !== false){
        foreach($boots as $b){
            $content .= 'require_once("' . $b . '");' . "\n";
        }
    }
    $resWriteBootstrapCache = @file_put_contents(AJXP_PLUGINS_BOOTSTRAP_CACHE, $content);
}
if (!isset($resWriteBootstrapCache) || $resWriteBootstrapCache !== false){
    require_once(AJXP_PLUGINS_BOOTSTRAP_CACHE);
}
?>
