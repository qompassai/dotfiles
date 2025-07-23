#!/usr/bin/env sh
# /qompassai/Shell/.profile.d/12-aliases.sh
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################

[[ $- == *i* ]] || return
alias ls='ls --color=auto'
alias grep='grep --color=auto'
alias pytest='/usr/bin/pytest -c ~/.config/pytest/pytest.ini'
alias spn='sudo pacman -Syyu --noconfirm'
alias psn='paru -Syyu --noconfirm'
alias cmx='chmod +x'
alias scrp='sudo chown -R $USER:$USER'

#Conda
alias conda='/opt/qai/miniconda3/bin/conda'

#Dovecot
alias dvp='doveadm -c ~/.config/dovecot/dovecot.conf pw -s SHA512-CRYPT'
alias doveadm="doveadm -c $DOVECOT_CONF"
#Lua
alias lua='/usr/bin/lua5.1'
#Git
alias g='git'
alias ga='git add'
alias gb='git branch'
alias gc='git commit'
alias gca='git commit --amend'
alias gco='git checkout'
alias gd='git diff'
alias gdc='git diff --cached'
alias gf='git fetch'
alias gl='git log --oneline --graph --decorate'
alias gm='git merge'
alias gp='git push'
alias gpum='git push -u origin main'
alias gpl='git pull'
alias gs='git status'
alias jj='jj'
alias jja='jj add'
alias jjc='jj commit'
alias jjco='jj checkout'
alias jjd='jj diff'
alias jjlog='jj log'
alias jjst='jj status'
#Go
alias go_linux_amd64='go_cross_simple linux amd64'
alias go_linux_arm64='go_cross_simple linux arm64'
alias go_linux_arm="go_cross_simple linux arm"
alias go_windows_amd64="go_cross_simple windows amd64"
alias go_windows_arm64="go_cross_simple windows arm64"
alias go_darwin_amd64="go_cross_simple darwin amd64"
alias go_darwin_arm64="go_cross_simple darwin arm64"
alias go_freebsd_amd64="go_cross_simple freebsd amd64"
alias go_linux_amd64_cgo="go_cross_zig linux amd64"
alias go_linux_arm64_cgo="go_cross_zig linux arm64"
alias go_windows_amd64_cgo="go_cross_zig windows amd64"
alias go_darwin_amd64_cgo="go_cross_zig darwin amd64"
alias go_darwin_arm64_cgo="go_cross_zig darwin arm64"
alias use_zig="use_compiler zig"
alias use_clang="use_compiler clang"
alias use_gcc="use_compiler gcc"
alias go_cross_help="print_go_cross_help"
#HF
alias hfd='HF_TOKEN=$(pass show hf) hfdownloader'
alias hflogin='hf login'
alias hflogout='hf logout'
alias hfdown='HF_TOKEN=$(pass show hf) hf download'
alias hfup='HF_TOKEN=$(pass show hf) hf upload'
alias hflist='HF_TOKEN=$(pass show hf) hf list'
alias hfscan='HF_TOKEN=$(pass show hf) hf scan-cache'
alias hfclean='HF_TOKEN=$(pass show hf) hf delete-cache'
alias hfwhoami='HF_TOKEN=$(pass show hf) hf whoami'
alias hfmodels='HF_TOKEN=$(pass show hf) hf list-models'
alias hfdatasets='HF_TOKEN=$(pass show hf) hf list-datasets'
alias hfspaces='HF_TOKEN=$(pass show hf) hf list-spaces'
alias hfqai='HF_TOKEN=$(pass show hf) hf download --repo-type model'
alias hfllama='HF_TOKEN=$(pass show hf) hf download meta-llama/'
alias hfmistral='HF_TOKEN=$(pass show hf) hf download mistralai/'
#JS
alias bun='bun'
alias bunx='bunx'
alias deno='deno'
alias ni='npm install'
alias nid='npm install --save-dev'
alias nig='npm install --global'
alias nr='npm run'
alias ns='npm start'
alias nt='npm test'
alias nv='node --version && npm --version'
alias pi='pnpm install'
alias pr='pnpm run'
alias px='pnpm exec'
alias ya='yarn add'
alias yad='yarn add --dev'
alias yag='yarn global add'
alias yr='yarn run'
alias ys='yarn start'
alias yt='yarn test'
#Neovim
alias nv='nvim'
alias sn='sudo -E nvim'
#alias nv='$HOME/.local/bin/nvim'
#alias sn='sudo -E '"$HOME"'/.local/bin/nvim'
alias sv='sudo -E vim'
#Ocaml
alias dune='dune'
alias dunebuilds='dune build'
alias duneexec='dune exec'
alias duneinstall='dune install'
alias dunetest='dune test'
alias ocaml='ocaml'
alias ocamldep='ocamldep'
alias ocamldoc='ocamldoc'
alias ocamlformat='ocamlformat'
alias ocamllsp='ocamllsp'
alias ocamlopt='ocamlopt'
alias opam='opam'
alias opaminstall='opam install'
alias opamlist='opam list'
alias opamshow='op'
#PHP
alias composer-clear-cache='composer clear-cache'
alias composer-global='composer global'
alias composer-install='composer install'
alias composer-outdated='composer outdated'
alias composer-self-update='composer self-update'
alias composer-update='composer update'
alias phpunit='phpunit'
alias phpinfo='php -i'
alias phplint='find . -type f -name "*.php" -exec php -l {} \;'
alias phpsrv='php -S localhost:8000'
alias phpbrew-init='source "$HOME/.phpbrew/bashrc"'
#Python
alias python='/usr/bin/python3.13'
alias python3='/usr/bin/python3.13'
alias pip3='/usr/bin/python3.13 -m pip'
alias pip='/usr/bin/pip'
alias pytest='/usr/bin/pytest'
#QPG
#alias qpg="/opt/QAI/qpg/bin/qpg"
#alias qpg-connect-connect="/opt/QAI/qpg/bin/qpg-agent"
#alias qpgconf="/opt/QAI/qpg/bin/qpgconf"
#alias qdirmngr="/opt/QAI/qpg/libexec/dirmngr"
#alias qpg-connect-agent="opt/QAI/qpg/bin/qpg-connect-agent"
alias qs='qsync'
#Shell
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'
alias c='clear'
alias df='df -h'
alias du='du -h'
alias g='git'
alias grep='grep --color=auto'
alias h='history'
alias l='ls -CF'
alias la='ls -A'
alias ll='ls -alF'
alias ls='ls --color=auto'
alias mkdir='mkdir -pv'
alias mv='mv -i'
alias ports='netstat -tulanp'
alias ps='ps aux'
alias rm='rm -i'
alias top='htop'
alias vi='vim'

#Tor
alias tor='tor -f ~/.config/sextant/torrc'
alias arti='arti'
alias nyx='nyx'
alias onionshare='onionshare'
alias onionshare-cli='onionshare-cli'
alias torbrowser='$TORBROWSER_HOME/Browser/start-tor-browser'
alias torcheck='curl --socks5 127.0.0.1:9050 https://check.torproject.org/api/ip'
alias torctl='tor --hash-password'
alias torid='tor --quiet --hash-password ""'
alias torlog='tail -f $TOR_LOG_DIR/tor.log'
alias tornewid='echo -e "AUTHENTICATE \"\"\r\nSIGNAL NEWNYM\r\nQUIT" | nc 127.0.0.1 9051'
alias torproxy='export ALL_PROXY=socks5://127.0.0.1:9050'
alias torstart='systemctl --user start tor'
alias torstatus='systemctl --user status tor'
alias torstop='systemctl --user stop tor'
alias torunproxy='unset ALL_PROXY HTTP_PROXY HTTPS_PROXY SOCKS_PROXY'
#Unbound
alias unbound='unbound'

#Zig
alias rzig=/opt/zig/bin/zig
