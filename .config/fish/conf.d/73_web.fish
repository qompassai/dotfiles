#!/usr/bin/env fish
# /qompassai/dotfiles/.config/fish/conf.d/73_web.fish
# Qompass AI Fish Web Config
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
alias myip='curl ifconfig.co'
alias localip="ip -o route get to 1.1.1.1 | sed -n 's/.*src \([0-9.]\+\).*/\1/p'"
alias whereami='curl ifconfig.co/json'
function random-name --description "Random name for registration on random websites. How about Helen Lovick? Roger Rice?"
    curl -s "https://randomuser.me/api/" | jq -r '.results[0].name.first + " " + .results[0].name.last'
end
function random-alias --description "Docker-like alias generator: `thirsty_mahavira`, `boring_heisenberg`. Don't know how to name file/project/branch/file? Use this!"
    curl -s https://frightanic.com/goodies_content/docker-names.php | tee /dev/tty | xclip -sel clip; and echo -e "\ncopied to clipboard"
end
function random-email --description "Random email for registration on random websites. Generate random email in one of Mailinator subdomains and provide link to check it. Useful when <http://bugmenot.com/> is not available."
    set domain (echo -e \
"notmailinator.com
veryrealemail.com
chammy.info
tradermail.info
mailinater.com
suremail.info
reconmail.com" | shuf -n1)
    set name (curl -s "https://randomuser.me/api/" | jq -r '.results[0].name.first + .results[0].name.last')
    set email $name@$domain
    printf "$email" | tee /dev/tty | xclip -sel clip
    echo -e "\ncopied to clipboard\nhttps://www.mailinator.com/v4/public/inboxes.jsp?to=$name"
end
function duckmails --description "Duck Mails! Woo-oo! Private Duck Address Generator"
    if not test -f "$HOME/keys/duck"
        echo "File at ~/keys/duck should contain token from dev tools on https://duckduckgo.com/email/"
        return 1
    end
    curl -s -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.3" 'https://quack.duckduckgo.com/api/email/addresses' -X POST -H "authorization: Bearer "(cat ~/keys/duck) -H 'content-type: application/json' | jq -r '.address + "@duck.com"' | tr -d '\n' | xclip -sel clip
    echo "Duck Mails! Woo-oo! (copied to clipboard):"
    echo (xclip -sel clip -o)
end

function random-password --description "Generate random password" --argument-names length
    test -n "$length"; or set length 13
    head /dev/urandom | tr -dc "[:alnum:]~!#\$%^&*-+=?./|" | head -c $length | tee /dev/tty | xclip -sel clip; and echo -e "\ncopied to clipboard"
end

function weather --description "Show weather"
    resize -s $LINES 125
    curl wttr.in/$argv
end

function xsh --description "Prepend this to command to explain its syntax i.e. `xsh iptables -vnL --line-numbers`"
    w3m -o confirm_qq=false "http://explainshell.com/explain?cmd=$argv"
end

function syn --description "Find synonyms for word"
    test -e ~/git/stuff/keys/bighugelabs || echo "Get API key at https://words.bighugelabs.com/account/getkey and put in "(status --current-filename)
    curl http://words.bighugelabs.com/api/2/(cat ~/git/stuff/keys/bighugelabs)/$argv/
end

function waitweb --description 'Wait until web resource is available. Useful when you are waiting for internet to get back, or Spring to start' --argument-names url
    set -q url || set url 'google.com'
    printf "Waithing for the $url"
    while not curl --output /dev/null --silent --head --fail "$url"
        printf '.'
        sleep 10
    end
    printf "\n$url is online!"
    notify-send -u critical "$url is online!"
end

function uselessfact --description "Print random useless fact. Makes checking if internet is awailable little less boring"
    curl -s https://uselessfacts.jsph.pl/api/v2/facts/random | jq .text
end

alias xkcd='curl -sL https://c.xkcd.com/random/comic/ | grep -Po "https:[^\"]*" | grep png | xargs curl -s | convert -negate -fuzz 10% -transparent black png: png:- | kitty +kitten icat'

alias albumart='sp metadata | grep -Po "(?<=url\|).*" | xargs curl -s | grep -Po "https:[^\"]*" | grep "i.scdn.co/image/" | head -1 | xargs curl -s | kitty +kitten icat'

function virustotal --description "Check file hash by virustotal.com"
    test -e ~/git/stuff/keys/virustotal || echo "Get API key at https://www.virustotal.com/gui/my-apikey and put in "(status --current-filename)
    curl -sL --request GET \
        --url https://www.virustotal.com/api/v3/files/(sha256sum $argv | cut -f 1 -d " ") \
        --header "x-apikey: "(cat ~/git/stuff/keys/virustotal) \
        | jq ".data .attributes .last_analysis_stats, .data .attributes .tags, .data .attributes .total_votes"
end
function raindrop --description "Create raindrop at raindrop.io"
    test -e $raindrop_key || echo "Create test token at https://app.raindrop.io/settings/integrations and put in $raindrop_key"
    set -l url $argv
    set -l raindrop_key ~/git/stuff/keys/raindrop
    set -l parse_response (curl -s -H "Authorization: Bearer "(cat $raindrop_key) "https://api.raindrop.io/rest/v1/import/url/parse?url=$url")
    set -l title (echo $parse_response | jq -r '.item.title')
    set -l excerpt (echo $parse_response | jq -r '.item.excerpt')
    set -l cover_image (echo $parse_response | jq -r '.item.cover')
    set -l type (echo $parse_response | jq -r '.item.type')
    set -l tags (echo $parse_response | jq -r '.item.meta.tags | join(",")')

    set -l create_response (curl -s -X POST \
    -H "Authorization: Bearer "(cat $raindrop_key) \
    -H "Content-Type: application/json" \
    -d '{
      "link": "'"$url"'",
      "title": "'"$title"'",
      "excerpt": "'"$excerpt"'",
      "cover": "'"$cover_image"'",
      "type": "'"$type"'",
      "tags": ["'"$tags"'"]
    }' \
    "https://api.raindrop.io/rest/v1/raindrop")

    if echo $create_response | jq -e '.result == true' >/dev/null
        echo Success
    else
        echo $create_response
    end
end
