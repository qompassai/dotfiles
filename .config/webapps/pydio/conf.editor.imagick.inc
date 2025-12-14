<?php
/*
 * /qompassai/dotfiles/.config/webapps/pydio/conf.editor.imagick.inc
 * Qompass AI Pydio Imagick Editor Config
 * Copyright (C) 2025 Qompass AI, All rights reserved
 ****************************************
 */
defined('AJXP_EXEC') or die('Access not allowed');
$DRIVER_CONF = [
    "IMAGE_MAGICK_CONVERT" => "/opt/local/bin/convert",
    "ADDITIONAL_ENV_PATH" => "",
    "UNOCONV" => "",
    "IM_THUMB_QUALITY" => "-quality 65 -density 150 -resize 250 -flatten",
    "IM_VIEWER_QUALITY" => "-quality 90 -density 250",
    "IM_CUSTOM_OPTIONS" => ""
];
?>
