<?php
/*
* /qompassai/dotfiles/.config/webapps/dokuwiki/mediameta.php
* Qompass AI DokuWiki MediaMeta Config
* Copyright (C) 2025 Qompass AI, All rights reserved
***********************************************************
 * References: http://www.dokuwiki.org/devel:templates:detail.php
 */
$fields = array(
    10 => array('Iptc.Headline',
                'img_title',
                'text'),
    20 => array('',
                'img_date',
                'date',
                array('Date.EarliestTime')),

    30 => array('',
                'img_fname',
                'text',
                array('File.Name')),

    40 => array('Iptc.Caption',
                'img_caption',
                'textarea',
                array('Exif.UserComment',
                      'Exif.TIFFImageDescription',
                      'Exif.TIFFUserComment')),

    50 => array('Iptc.Byline',
                'img_artist',
                'text',
                array('Exif.TIFFArtist',
                      'Exif.Artist',
                      'Iptc.Credit')),

    60 => array('Iptc.CopyrightNotice',
                'img_copyr',
                'text',
                array('Exif.TIFFCopyright',
                      'Exif.Copyright')),

    70 => array('',
                'img_format',
                'text',
                array('File.Format')),

    80 => array('',
                'img_fsize',
                'text',
                array('File.NiceSize')),

    90 => array('',
                'img_width',
                'text',
                array('File.Width')),

    100 => array('',
                'img_height',
                'text',
                array('File.Height')),

    110 => array('',
                'img_camera',
                'text',
                array('Simple.Camera')),

    120 => array('Iptc.Keywords',
                'img_keywords',
                'text',
                array('Exif.Category')),
);
?>
