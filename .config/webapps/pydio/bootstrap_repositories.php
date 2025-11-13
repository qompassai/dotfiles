<?php
 /*
* /qompassai/dotfiles/.config/webapps/pydio/bootstrap_repositories.php
* Qompass AI Pydio BootStrap Repositories Config
* Copyright (C) 2025 Qompass AI, All rights reserved
***********************************************************************
 */
defined('AJXP_EXEC') or die( 'Access not allowed');
$REPOSITORIES[0] = array(
    "DISPLAY"		=>	"Default Files",
    "DISPLAY_ID"    =>  430,
    "DESCRIPTION_ID"=>  475,
    "AJXP_SLUG"		=>  "default",
    "DRIVER"		=>	"fs",
    "DRIVER_OPTIONS"=> array(
        "PATH"			=>	"AJXP_DATA_PATH/files",
        "CREATE"		=>	true,
        "RECYCLE_BIN" 	=> 	'recycle_bin',
        "CHMOD_VALUE"   =>  '0600',
        "DEFAULT_RIGHTS"=>  "",
        "PAGINATION_THRESHOLD" => 500,
        "PAGINATION_NUMBER" => 200,
        "META_SOURCES"		=> array(
            "metastore.serial"=> array(
                "METADATA_FILE"	=> ".ajxp_meta",
                "METADATA_FILE_LOCATION" => "infolders"
            ),
            "meta.user"     => array(
                "meta_fields"		=> "tags",
                "meta_labels"		=> "Tags",
                "meta_visibility"   => "hidden"
            ),
            "meta.filehasher"   => array(),
            "meta.watch"        => array(),
            "meta.syncable"     => array("REPO_SYNCABLE" => true),
            "meta.exif"   => array(
                "meta_fields" => "COMPUTED_GPS.GPS_Latitude,COMPUTED_GPS.GPS_Longitude",
                "meta_labels" => "Latitude,Longitude"
            ),
            "index.lucene" => array(
                "index_meta_fields" => "tags"
            ),
        )
    ),

);
$REPOSITORIES[1] = array(
    "DISPLAY"		=>	"My Files",
    "DISPLAY_ID"    =>  432,
    "DESCRIPTION_ID"=>  476,
    "AJXP_SLUG"		=>  "my-files",
    "DRIVER"		=>	"fs",
    "DRIVER_OPTIONS"=> array(
        "PATH"			=>	"AJXP_DATA_PATH/personal/AJXP_USER",
        "CREATE"		=>	true,
        "RECYCLE_BIN" 	=> 	'recycle_bin',
        "CHMOD_VALUE"   =>  '0600',
        "DEFAULT_RIGHTS"=>  "rw",
        "PAGINATION_THRESHOLD" => 500,
        "PAGINATION_NUMBER" => 200,
        "META_SOURCES"		=> array(
            "metastore.serial"=> array(
                "METADATA_FILE"	=> ".ajxp_meta",
                "METADATA_FILE_LOCATION" => "infolders"
            ),
            "meta.user"     => array(
                "meta_fields"		=> "tags",
                "meta_labels"		=> "Tags",
                "meta_visibility"   => "hidden"
            ),
            "meta.filehasher"   => array(),
            "meta.watch"        => array(),
            "meta.syncable"     => array("REPO_SYNCABLE" => true),
            "meta.exif"   => array(
                "meta_fields" => "COMPUTED_GPS.GPS_Latitude,COMPUTED_GPS.GPS_Longitude",
                "meta_labels" => "Latitude,Longitude"
            ),
            "index.lucene" => array(
                "index_meta_fields" => "tags",
                "repository_specific_keywords" => "AJXP_USER",
            )
        )
    ),

);
$REPOSITORIES["ajxp_home"] = array(
    "DISPLAY"		    =>	"Welcome",
    "AJXP_SLUG"		    =>  "welcome",
    "DISPLAY_ID"		=>	"user_home.title",
    "DESCRIPTION_ID"	=>	"user_home.desc",
    "DRIVER"		    =>	"ajxp_home",
    "DRIVER_OPTIONS"    => array(
        "DEFAULT_RIGHTS" => "rw"
    )
);
$REPOSITORIES["inbox"] = array(
    "DISPLAY"		    =>	"Inbox",
    "DISPLAY_ID"        =>  "inbox_driver.12",
    "DESCRIPTION_ID"	=>	"inbox_driver.13",
    "AJXP_SLUG"		    =>  "inbox",
    "DRIVER"		    =>	"inbox",
    "DRIVER_OPTIONS"    => array(
        "DEFAULT_RIGHTS" => "r",
        "META_SOURCES"   => array(
            "metastore.serial"=> array(
                "METADATA_FILE"	=> ".ajxp_meta",
                "METADATA_FILE_LOCATION" => "infolders"
            ),
            "meta.watch"    => array()
        )
    )
);
$REPOSITORIES["ajxp_conf"] = array(
    "DISPLAY"		    =>	"Settings",
    "AJXP_SLUG"		    =>  "settings",
    "DISPLAY_ID"		=>	"165",
    "DESCRIPTION_ID"	=>	"506",
    "DRIVER"		    =>	"ajxp_conf",
    "DRIVER_OPTIONS"    => array()
);
$REPOSITORIES["fs_template"] = array(
    "DISPLAY"		=>	"Sample Template",
    "DISPLAY_ID"    =>  431,
    "IS_TEMPLATE"	=>  true,
    "DRIVER"		=>	"fs",
    "DRIVER_OPTIONS"=> array(
        "CREATE"		=>	true,
        "RECYCLE_BIN" 	=> 	'recycle_bin',
        "CHMOD_VALUE"   =>  '0600',
        "PAGINATION_THRESHOLD" => 500,
        "PAGINATION_NUMBER" => 200,
        "PURGE_AFTER"       => 0,
        "CHARSET"           => "",
        "META_SOURCES"		=> array(
            "metastore.serial"=> array(
                "METADATA_FILE"	=> ".ajxp_meta",
                "METADATA_FILE_LOCATION" => "infolders"
            ),
            "meta.user"     => array(
                "meta_fields"		=> "tags",
                "meta_labels"		=> "Tags",
                "meta_visibility"   => "hidden"
            ),
            "meta.filehasher"   => array(),
            "meta.watch"        => array(),
            "meta.syncable"     => array(),
            "meta.exif"   => array(
                "meta_fields" => "COMPUTED_GPS.GPS_Latitude,COMPUTED_GPS.GPS_Longitude",
                "meta_labels" => "Latitude,Longitude"
            ),
            "index.lucene" => array(
                "index_meta_fields" => "tags"
            )
        )
    ),

);
if(!is_file(AJXP_PLUGINS_REPOSITORIES_CACHE)){
    $content = "<?php \n";
    $boots = glob(AJXP_INSTALL_PATH."/".AJXP_PLUGINS_FOLDER."/*/repositories.php");
    if($boots !== false){
        foreach($boots as $b){
            $content .= 'require_once("'.$b.'");'."\n";
        }
    }
    $resWriteRepoCache = @file_put_contents(AJXP_PLUGINS_REPOSITORIES_CACHE, $content);
}
if(!isSet($resWriteRepoCache) || $resWriteRepoCache === true){
    include_once(AJXP_PLUGINS_REPOSITORIES_CACHE);
}
?>
