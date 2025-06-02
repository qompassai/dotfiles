# /qompassai/dotfiles/fish/conf.d/abbreviations.fish
# Fish Abbreviations
# Copyright (C) 2025 Qompass AI, All rights reserved
#---------------------------------------------------

if status is-interactive
    abbr -a spn 'sudo pacman -Syyu --noconfirm'
    abbr -a psn 'paru -Syyu --noconfirm'
    abbr -a cmx 'chmod +x'
    abbr -a scrp 'sudo chown -R $USER:$USER'
    abbr -a .. 'cd ..'
    abbr -a ... 'cd ../..'
    abbr -a .... 'cd ../../..'
    abbr -a ll 'ls -alF'
    abbr -a la 'ls -A'
    abbr -a l 'ls -CF'
    # Git
    abbr -a g git
    abbr -a ga 'git add'
    abbr -a gb 'git branch'
    abbr -a gc 'git commit'
    abbr -a gca 'git commit --amend'
    abbr -a gco 'git checkout'
    abbr -a gd 'git diff'
    abbr -a gdc 'git diff --cached'
    abbr -a gf 'git fetch'
    abbr -a gl 'git log --oneline --graph --decorate'
    abbr -a gm 'git merge'
    abbr -a gp 'git push'
    abbr -a gpum 'git push -u origin main'
    abbr -a gpl 'git pull'
    abbr -a gs 'git status'

    # Python
    abbr -a python3 '/usr/bin/python3.13'
    abbr -a pip3 '/usr/bin/python3.13 -m pip'

    # Neovim
    abbr -a nv nvim
    abbr -a sn 'sudo -E nvim'
    abbr -a sv 'sudo -E vim'

    # HuggingFace 
    abbr -a hfd 'HF_TOKEN=(pass show hf) hfdownloader'
    abbr -a hfdown 'HF_TOKEN=(pass show hf) hf download'
    abbr -a hfup 'HF_TOKEN=(pass show hf) hf upload'
    abbr -a hfwhoami 'HF_TOKEN=(pass show hf) hf whoami'

    # Other useful ones
    abbr -a c clear
    abbr -a h history
    abbr -a top htop
    abbr -a ports 'netstat -tulanp'
    abbr -a df 'df -h'
    abbr -a du 'du -h'
end
