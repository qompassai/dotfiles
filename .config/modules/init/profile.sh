# shellcheck shell=sh

# get current shell name by querying shell variables or looking at parent
# process name
if [ -n "${BASH:-}" ]; then
   if [ "${BASH##*/}" = 'sh' ]; then
      shell='sh'
   else
      shell='bash'
   fi
elif [ -n "${ZSH_NAME:-}" ]; then
   shell=$ZSH_NAME
else
   shell=$(/usr/bin/basename "$(/usr/bin/ps -p $$ -ocomm=)")
fi

if [ -f "/etc/modules/init/$shell" ]; then
   . "/etc/modules/init/$shell"
else
   . '/etc/modules/init/sh'
fi
