<?php
/**
 * SimpleID configuration file.
 *
 * @package simpleid
 *
 */
/*
 * $Id$
 *
 */


 * <code>
 *   define('SIMPLEID_BASE_URL', 'http://www.example.com');
 *   define('SIMPLEID_BASE_URL', 'http://www.example.com:8888');
 *   define('SIMPLEID_BASE_URL', 'http://www.example.com/simpleid');
 *   define('SIMPLEID_BASE_URL', 'https://www.example.com:8888/simpleid');
 * </code>
define('SIMPLEID_BASE_URL', 'http://www.example.com');
define('SIMPLEID_CLEAN_URL', false);
define('SIMPLEID_IDENTITIES_DIR', '../identities');
define('SIMPLEID_CACHE_DIR', '../cache');
define('SIMPLEID_STORE', 'filesystem');
define('SIMPLEID_STORE_DIR', '../store');
define('SIMPLEID_ALLOW_PLAINTEXT', false);
define('SIMPLEID_ALLOW_AUTOCOMPLETE', false);
define('SIMPLEID_VERIFY_RETURN_URL_USING_REALM', true);
define('SIMPLEID_LOCALE', 'en');
define('SIMPLEID_DATE_TIME_FORMAT', '%Y-%m-%d %H:%M:%S %Z');
define('SIMPLEID_ASSOC_EXPIRES_IN', 3600);
define('SIMPLEID_EXTENSIONS', 'sreg,ui');
define('SIMPLEID_LOGFILE', '');
define('SIMPLEID_LOGLEVEL', 4);
?>
