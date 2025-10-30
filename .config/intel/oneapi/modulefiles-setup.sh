#!/usr/bin/env bash
# /qompassai/dotfiles/.config/intel/oneapi/modulefiles-setup.sh
# Qompass AI Intel OneAPI ModuleFiles Setup Config
# Copyright (C) 2025 Qompass AI, All rights reserved
##################################################################
# shellcheck shell=sh
script_name=$(basename -- "$0")

usage() {
  echo "  "
  echo "usage: ${script_name}" '[--output-dir=dir]' '[--help]'
  echo "  "
  echo "Scans the oneAPI installation folder for available modulefiles and organizes"
  echo "them into a single folder that can be added to the \$MODULEPATH environment"
  echo "variable or by using the 'module use' command. For each tool or library that"
  echo "is found in the oneAPI installation folder, every version available for that"
  echo "tool or library is added to the output folder."
  echo "  "
  echo "  --output-dir=path/to/folder/name"
  echo "    Specify path/name of folder to contain oneAPI modulefile links."
  echo "    Default output location is the '${HOME}/modulefiles' folder."
  echo "      e.g., --output-dir=~/intel-oneapi-modulefiles"
  echo "  "
  echo "  --force"
  echo "    Force replacement of modulefiles output directory without warning."
  echo "  "
  echo "  --ignore-latest"
  echo "    Ignore (do not include) the \"latest\" version symlink in the list of"
  echo "    modulefiles created in the modulefiles output directory. Add only the"
  echo "    versioned modulefiles into the modulefiles output directory."
  echo "  "
  echo "  --help"
  echo "    Display this help message and exit."
  echo "  "
}

# TODO: add support for input folder option
#   echo "  --input-dir=path/to/oneapi/install/dir"
#   echo "    Specify oneAPI installation directory to be scanned."
#   echo "    Multiple instances of --input=dir are allowed."
#   echo "    Defaults to folder containing this script."
#   echo "  "


# ############################################################################

# Get absolute path to script. **NOTE:** `readlink` is not a POSIX command!!
# Uses `readlink` to remove links and `pwd -P` to turn into an absolute path.
# see also: https://stackoverflow.com/a/12145443/2914328

# Usage:
#   script_dir=$(get_script_path "$script_rel_path")
#
# Inputs:
#   script/relative/pathname/scriptname
#
# Outputs:
#   /script/absolute/pathname

# executing function in a *subshell* to localize vars and effects on `cd`
get_script_path() (
  script="$1"
  while [ -L "$script" ] ; do
    # combining next two lines fails in zsh shell
    script_dir=$(command dirname -- "$script")
    script_dir=$(command cd "$script_dir" && command pwd -P)
    script="$(readlink "$script")"
    case $script in
      (/*) ;;
       (*) script="$script_dir/$script" ;;
    esac
  done
  # combining next two lines fails in zsh shell
  script_dir=$(command dirname -- "$script")
  script_dir=$(command cd "$script_dir" && command pwd -P)
  echo "$script_dir"
)


# ###########################################################################

# Make sure we are being executed, not sourced.
# Making this detection for a variety of /bin/sh impersonators is overkill.
# If it becomes necessary to do that, we can add support right here.

# if [ "$0" != "${BASH_SOURCE}" ] ; then
#   echo "  "
#   echo ":: ERROR: Incorrect usage: \"$script_name\" must be executed, not sourced." ;
#   usage
#   return 255 2>/dev/null || exit 255
# fi


# ############################################################################

# Interpret command-line arguments passed to this script.
# Set the default location for the final modulefiles output folder.
# see https://unix.stackexchange.com/a/258514/103967

opthelp=0
optforce=0
optignorelatest=0
script_root=$(get_script_path "${0}")
modulesoutdir=${HOME}/modulefiles
#modulesoutdir=${script_root}/modulefiles

for arg do
  shift
  case "$arg" in
    (--help)
      opthelp=1
      ;;
    (--force)
      optforce=1
      ;;
    (--ignore-latest)
      optignorelatest=1
      ;;
    (--output-dir=*)
      modulesoutdir="$(expr "$arg" : '--output-dir=\(.*\)')"
      ;;
    (*)
      set -- "$@" "$arg"
      ;;
  esac
  # echo "\$@ = " "$@"
done

# Fix pesky '~' alias, if $modulesoutdir happens to start with it.
modulesoutdir=$(printf "%s" "$modulesoutdir" | sed -e "s:^\~:$HOME:")

if [ "$opthelp" != "0" ] ; then
  usage
  return 254 2>/dev/null || exit 254
fi


# ############################################################################

# Create the output modulefiles directory.
# Clean it up in case of a pre-existing copy.

echo ":: Initializing oneAPI modulefiles folder ..."
echo ":: Removing any previous oneAPI modulefiles folder content."

# Create the modulefiles output folder.
# Ask user if okay to clean a pre-existing modulefiles output folder.
# Using the "--force" command-line option assumes answer is "yes."

optyn=n
if [ -e "$modulesoutdir" ] && [ "$optforce" = "0" ] ; then
  while true ; do
    echo ":: WARNING: \"$modulesoutdir\" exists and will be deleted."
    command -p read -p "   Okay to proceed with deletion? [yn] " optyn
    case $optyn in
      ([Yy])  optforce=1 ; break ;;
      ([Nn])  optforce=0 ; break ;;
      (*)     echo "   Please answer y or n." ;;
    esac
  done
fi

if ! command -p mkdir -p "$modulesoutdir" ; then
  echo ":: ERROR: Creation of \"$modulesoutdir\" folder failed."
  echo "   Can be caused by read-only target or existing file of same name."
  exit 1
fi
if [ "$optforce" = "1" ] ; then
  if ! command -p rm -rf "$modulesoutdir"/* ; then
    echo ":: ERROR: Deletion of \"$modulesoutdir\" folder failed."
    echo "   Can be caused by read-only target or existing file of same name."
    exit 2
  fi
fi


# ############################################################################

# Process oneAPI components.
# Scan for modulefiles and create symlinks in the modulefiles output folder.
# Usage of `find ... -mindepth ... -maxdepth` may fail on BSD (e.g., macOS).
# TODO: `find` options usage described above is not POSIX compliant.
# TODO: May be worth considering use of `ls` instead of `find`.

echo ":: Generating oneAPI modulefiles folder links."

# each subdirectory is a potential oneAPI "component"
# make sure each "component" variable ends with a trailing '/' character
for component in $(command -p ls -d "$script_root"/*/) ; do
  # find false positive "unified" directory "component", skip $component/etc
  if [ -d "${component}/etc" ] ; then continue ; fi

  versiondircount=$(find "$component" -mindepth 1 -maxdepth 1 -type d | wc -l)
  if [ "$versiondircount" -gt 0 ] ; then

    # each subdirectory of a component is a version specifier
    # using 'ls -d' rather than find because it sees symlinked dirs
    for versiondir in $(command -p ls -d "$component"*/) ; do
      version=$(basename "$versiondir")
      modulefilesindir=${versiondir}modulefiles

      # if --ignore-latest option was provided, skip "latest" versiondir
      if [ "$version" = "latest" ] && [ "$optignorelatest" != "0" ] ; then continue ; fi

      # if we find a directory named modulefiles look for modulefiles
      if [ -d "$modulefilesindir" ] ; then
        files="$modulefilesindir/*"
        for modulefile in $files ; do
          modulename=$(basename "$modulefile")

          # resolve tcl scripts that are symlinked into <cmp-root>/modulefiles
          if [ -h "$modulefile" ] ; then
            modulefile="$(get_script_path "$modulefile")/${modulename}"
            if ! [ -e "$modulefile" ] ; then continue ; fi
          fi

          echo ":: ${modulename}/${version} -> $modulefile"

          # create module directory
          if [ ! -d "$modulesoutdir/$modulename" ] ; then
            if ! command -p mkdir -p "$modulesoutdir/$modulename" ; then
              echo ":: ERROR: Creation of \"$modulesoutdir/$modulename\" folder failed."
              echo "   Can be caused by read-only target or existing file of same name."
              return 3 2>/dev/null || exit 3
            fi
          fi
          # create a symlink to the modulefile located in the install dir
          # TODO: -f option may be dangerous, seek alternate option
          if ! command -p ln -fs "$modulefile" "$modulesoutdir/$modulename/$version" ; then
            echo ":: ERROR: Creation of \"$modulesoutdir/$modulename/$version\" symlink failed."
            echo "   Can be caused by read-only target or existing file of same name."
            return 4 2>/dev/null || exit 4
          fi
        done
      fi
    done
  fi
done


# each subdirectory is a potential oneAPI "component"
# make sure each "component" variable ends with a trailing '/' character
for component in $(command -p ls -d "$script_root"/*/) ; do
  # find false positive "unified" directory "component", skip $component/etc
  if [ -d "${component}/etc" ] ; then continue ; fi

  versiondircount=$(find "$component" -mindepth 1 -maxdepth 1 -type d | wc -l)
  if [ "$versiondircount" -gt 0 ] ; then

    # each subdirectory of a component is a version specifier
    # using 'ls -d' rather than find because it sees symlinked dirs
    for versiondir in $(command -p ls -d "$component"*/) ; do
      version=$(basename "$versiondir")

      # if --ignore-latest option was provided, skip "latest" versiondir
      if [ "$version" = "latest" ] && [ "$optignorelatest" != "0" ] ; then continue ; fi

      # skip any old-layout components
      if [ ! -d "${versiondir}etc/modulefiles/" ] ; then continue ; fi

      # find all tcl scripts inside etc/modulefiles/$modulename folder
      for modulename in $(command -p ls -d "${versiondir}etc/modulefiles/"*) ; do
        if [ -d "$modulename" ] ; then
          for modulever in $(command -p ls -d "$modulename/"*) ; do

            modname=$(basename "$(dirname "$modulever")")
            # skip "oneapi" modulefile, it only works in a "unified" layout
            if [ "$modname" = "oneapi" ] ; then continue ; fi
            if [ "$version" = "latest" ] ; then
              modver=latest
            else
              modver=$(basename "$modulever")
            fi
            echo ":: ${modname}/${modver} -> $modulever"

            # create module directory
            if [ ! -d "$modulesoutdir/$modname" ] ; then
              if ! command -p mkdir -p "$modulesoutdir/$modname" ; then
                echo ":: ERROR: Creation of \"$modulesoutdir/$modname\" folder failed."
                echo "   Can be caused by read-only target or existing file of same name."
                # shellcheck disable=SC2317
                return 3 2>/dev/null || exit 5
              fi
            fi
            # create a symlink to the modulefile located in the install dir
            # TODO: -f option may be dangerous, seek alternate option
            if ! command -p ln -fs "$modulever" "$modulesoutdir/$modname/$modver" ; then
              echo ":: ERROR: Creation of \"$modulesoutdir/$modname/$modver\" symlink failed."
              echo "   Can be caused by read-only target or existing file of same name."
              # shellcheck disable=SC2317
              return 4 2>/dev/null || exit 6
            fi
          done
        fi
      done
    done
  fi
done


echo ":: oneAPI modulefiles folder initialized."
echo ":: oneAPI modulefiles folder is here: \"$modulesoutdir\""
