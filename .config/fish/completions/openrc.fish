set -l openrc_files (ls ~/.openrc/files/ -1)

function __fish_complete_openrc_delegated_command
  set -l tokens (commandline -opc) (commandline -ct)
  set -e tokens[1] # Remove `openrc`
  set -e tokens[1] # Remove filename

  if test -n "$tokens"
    __fish_complete_subcommand --commandline $tokens
    return 0
  end

  return 1
end

# First positional argument is the openrc filename
complete -c openrc -f -n "not __fish_seen_subcommand_from $openrc_files" -a "$openrc_files"

# Rest is the delegate
complete -c openrc -f -n "__fish_seen_subcommand_from $openrc_files" -x -a "(__fish_complete_openrc_delegated_command)"

# In case it is not on PATH
complete -c ./openrc -w openrc
