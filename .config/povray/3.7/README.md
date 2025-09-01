<!-- README.md -->
<!-- Qompass AI - [Add description here] -->
<!-- Copyright (C) 2025 Qompass AI, All rights reserved -->
<!-- ---------------------------------------- -->
; /qompassai/dotfiles/povray/3.7/povray.ini
; Qompass AI POV-Ray Config
; Copyright (C) 2025 Qompass AI, All rights reserved
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

;                     PERSISTENCE OF VISION RAY TRACER
;
;                           POV-Ray VERSION 3.7
;
;                         SAMPLE POVRAY.INI FILE
;
;  The general form of the options is "Variable=value".  Everything 
;  between the equals sign and the end of the line is considered part 
;  of the value.  The spacing and layout is free-form but only one option 
;  per line is allowed.  Variables and values are not case-sensitive.  
;
;  Note: characters after a semi-colon are treated as a comment
;
;  Traditional POV-Ray switches beginning with + or - are also allowed
;  and they may be given with more than one switch per line.  
;
;  Add your own options at the bottom and/or edit these to suit. See the
;  general documentation for full instructions on how to use INI options.
;
; Width of image in pixels.  Accepts integer values.
;
Width = 800
;
;
; Height of image in pixels.  Accepts integer values.
;
Height = 600
;
; Sets minimum number of objects before auto bounding kicks in.
;
Bounding_Threshold = 3
;
;
; Turn display on
Display=On
;
; Turn verbose mode on
Verbose=On
;
;
; Specify path to search for any files not found in current directory.
; For example: Library_Path="C:\Program Files\POV-Ray for Windows\include"
; There may be some entries already here; if there are they were
; probably added by the install process or whoever set up the
; software for you. At the least you can expect an entry that
; points to the standard POV-Ray include files directory; on
; some operating systems there may also be one which points to
; the system's fonts directory.
;
; Note that some platforms (e.g. Windows, unless this feature is
; turned off via the configuration file) will automatically append
; standard locations like those mentioned above to the library
; path list after reading this file, so in those cases you don't
; necessarily have to have anything at all here.
;

;; Search path for #include source files or command line ini files not
;; found in the current directory.  New directories are added to the
;; search path, up to a maximum of 25.

Library_Path="/usr/share/povray-3.7"
Library_Path="/usr/share/povray-3.7/ini"
Library_Path="/usr/share/povray-3.7/include"

;; File output type control.
;;     T    Uncompressed Targa-24
;;     C    Compressed Targa-24
;;     P    UNIX PPM
;;     N    PNG (8-bits per colour RGB)
;;     Nc   PNG ('c' bit per colour RGB where 5 <= c <= 16)

Output_to_File=true
Output_File_Type=N8             ;; (+/-Ftype)

# povray.conf
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;
;                     PERSISTENCE OF VISION RAY TRACER
;
;                           POV-Ray VERSION 3.7
;
;                         SAMPLE POVRAY.CONF FILE
;                      FOR I/O RESTRICTIONS SETTINGS
;
;
; The general form of the options is:
;
; [Section]
; setting
;
; Note: characters after a semi-colon are treated as a comment.
;
; This file is used primarily to define security settings, i.e. to
; restrict reading and writing of files and running of scripts beyond
; the security provided by the file system.  Regardless of the settings
; in this file, POV-Ray will not allow users to read files they would
; not ordinarily be allowed to read, write files they would not
; ordinarily be allowed to write, or execute files they would not
; ordinarily be allowed to execute, unless someone has made the binary
; setuid or setgid.
;
; POV-Ray will look in two places for this file: in a system-wide directory
; (typically /usr/local/etc/povray/3.7/povray.conf) and in the user's home
; directory (as ~/.povray/3.7/povray.conf).  POV-Ray will always use the
; most strict version of what is specified; user settings can only make
; security more strict.
;
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;


; [File I/O Security] determines whether POV-Ray will be allowed to perform
; read-write operations on files.  Specify one of the 3 following values:
; - "none" means that there are no restrictions other than those enforced
;   by the file system, i.e. normal UNIX file and directory permissions.
; - "read-only" means that files may be read without restriction.
; - "restricted" means that files access is subject to restrictions as
;   specified in the rest of this file.  See the other variables for details.

[File I/O Security]
;none       ; all read and write operations on files are allowed.
;read-only  ; uses the "read+write" directories for writing (see below).
restricted  ; uses _only_ "read" and "read+write" directories for file I/O.


; [Shellout Security] determines whether POV-Ray will be allowed to call
; scripts (e.g. Post_Frame_Command) as specified in the documentation.
; Specify one of the 2 following values:
; - "allowed" means that shellout will work as specified in the documentation.
; - "forbidden" means that shellout will be disabled.

[Shellout Security]
;allowed
forbidden


; [Permitted Paths] specifies a list of directories for which reading or
; reading + writting is permitted (in those directories and optionnally
; in their descendents).  Any entry of the directory list is specified on
; a single line.  These paths are only used when the file I/O security
; is enabled (i.e. "read-only" or "restricted").
;
; The list entries must be formatted as following:
;   read = directory	     ; read-only directory
;   read* = directory        ; read-only directory including its descendents
;   read+write = directory   ; read/write directory
;   read+write* = directory  ; read/write directory including its descendents
; where directory is a string (to be quoted or doubly-quoted if it contains
; space caracters; see the commented example below).  Any number of spaces
; can be placed before and after the equal sign.  Read-only and read/write
; entries can be specified in any order.
;
; Both relative and absolute paths are possible (which makes "." particularly
; useful for defining the current working directory).  The POV-Ray install
; directory (e.g. /usr/local/share/povray-3.7 or /usr/share/povray-3.7)
; can be specified with "%INSTALLDIR%".  The install directory and its
; descendents are typically only writable by root; therefore you should not
; specify "%INSTALLDIR%" in read/write directory paths.  The user home
; directory can be specified with "%HOME%".
;
; Note that since user-level restrictions are at least as strict as system-
; level restrictions, any paths specified in the system-wide povray.conf
; will also need to be specified in the user povray.conf file.

[Permitted Paths]
;read = "/this/directory/contains space caracters"
read* = %INSTALLDIR%/include
read* = %INSTALLDIR%/scenes
read* = %INSTALLDIR%/../../etc
read* = %HOME%
read+write* = /tmp
read+write  = .
