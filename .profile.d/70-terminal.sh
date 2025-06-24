#!/usr/bin/env bash
export SHELL=/usr/bin/fish
case "${TERM_PROGRAM:-}" in
    Ghostty|ghostty)
        export SNACKS_GHOSTTY=true
        export TERM_PROGRAM=Ghostty
        ;;
    foot)
        export SNACKS_FOOT=true
        export TERM_PROGRAM=foot
        ;;
    kitty)
        export SNACKS_KITTY=true
        export TERM_PROGRAM=kitty
        ;;
    alacritty)
        export SNACKS_ALACRITTY=true
        export TERM_PROGRAM=alacritty
        ;;
esac

if [ -z "${TERM_PROGRAM:-}" ]; then
    case "${TERM}" in
        xterm-ghostty)
            export SNACKS_GHOSTTY=true
            export TERM_PROGRAM=Ghostty
            ;;
        foot)
            export SNACKS_FOOT=true
            export TERM_PROGRAM=foot
            ;;
        xterm-kitty)
            export SNACKS_KITTY=true
            export TERM_PROGRAM=kitty
            ;;
        alacritty)
            export SNACKS_ALACRITTY=true
            export TERM_PROGRAM=alacritty
            ;;
        xterm*|XTERM*)
            export SNACKS_XTERM=true
            export TERM_PROGRAM=xterm
            ;;
    esac
fi
