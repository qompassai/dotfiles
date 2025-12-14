if [[ -o interactive ]]; then
  [[ ! -r '/home/phaedrus/.opam/opam-init/complete.zsh' ]] || source '/home/phaedrus/.opam/opam-init/complete.zsh' > /dev/null 2> /dev/null

  [[ ! -r '/home/phaedrus/.opam/opam-init/env_hook.zsh' ]] || source '/home/phaedrus/.opam/opam-init/env_hook.zsh' > /dev/null 2> /dev/null
fi

[[ ! -r '/home/phaedrus/.opam/opam-init/variables.sh' ]] || source '/home/phaedrus/.opam/opam-init/variables.sh' > /dev/null 2> /dev/null
