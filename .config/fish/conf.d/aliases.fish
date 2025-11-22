abbr -a rm       'rm -Iv'
abbr -a cp       'cp -iv'
abbr -a mv       'mv -iv'
abbr -a gpu      'watch -n 1 nvidia-smi'
abbr -a ls       'ls --color=auto'
abbr -a g        'git'
abbr -a ga       'git add'
abbr -a gb       'git branch'
abbr -a gc       'git commit'
abbr -a gca      'git commit --amend'
abbr -a gco      'git checkout'
abbr -a gd       'git diff'
abbr -a gdc      'git diff --cached'
abbr -a gf       'git fetch'
abbr -a gl       'git log --oneline --graph --decorate'
abbr -a gm       'git merge'
abbr -a gp       'git push'
abbr -a gpum     'git push -u origin main'
abbr -a gpl      'git pull'
abbr -a gs       'git status'
abbr -a luarocks 'luarocks --lua-version=5.1'
abbr -a ni       'npm install'
abbr -a nid      'npm install --save-dev'
abbr -a nig      'npm install --global'
abbr -a nr       'npm run'
abbr -a ns       'npm start'
abbr -a nt       'npm test'
abbr -a nv       'nvim'
abbr -a pag      'pnpm add -g'
abbr -a pr       'pnpm run'
abbr -a px       'pnpm exec'
abbr -a ya       'yarn add'
abbr -a yad      'yarn add --dev'
abbr -a yag      'yarn global add'
abbr -a yr       'yarn run'
abbr -a ys       'yarn start'
abbr -a yt       'yarn test'
function spn
    sudo pacman -Syyu --noconfirm $argv
end
function psn
    paru -Syyu --noconfirm $argv
end
function cmx
    chmod +x $argv
end
function scrp
    sudo chown -R $USER:$USER $argv
end
abbr -a sn 'sudo -E nvim'
abbr -a sv 'sudo -E vim'
abbr -a use_zig   'use_compiler zig'
abbr -a use_clang 'use_compiler clang'
abbr -a use_gcc   'use_compiler gcc'
abbr -a go_cross_help 'print_go_cross_help'
function grep
    command grep --color=auto $argv
end
