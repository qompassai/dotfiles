#!/usr/bin/env fish
# ~/.config/fish/convert_aliases.fish
# -----------------------------------
# Copyright (C) 2025 Qompass AI, All rights reserved

function convert_alias_to_fish
    set alias_line $argv[1]

    set alias_name (echo $alias_line | sed "s/alias \([^=]*\)=.*/\1/")
    set alias_cmd (echo $alias_line | sed "s/alias [^=]*='\(.*\)'/\1/" | sed 's/\\$//')

    echo "function $alias_name"
    echo "    $alias_cmd \$argv"
    echo end
    echo ""
end

grep "^alias " /qompassai/Shell/.profile.d/12-aliases.sh | while read line
    convert_alias_to_fish "$line"
end
