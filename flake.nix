{
  description = "Qompass AI Dotfiles Flake";
  inputs = {
    devshell.url = "github:numtide/devshell";
    devshell.inputs.nixpkgs.follows = "nixpkgs";
    flake-compat.url = "github:edolstra/flake-compat";
    flake-compat.flake = false;
    flake-parts.url = "github:hercules-ci/flake-parts";
    flake-parts.inputs.nixpkgs-lib.follows = "nixpkgs";
    treefmt-nix.url = "github:numtide/treefmt-nix";
    treefmt-nix.inputs.nixpkgs.follows = "nixpkgs";
    nvfetcher.url = "github:berberman/nvfetcher";
    nvfetcher.inputs.nixpkgs.follows = "nixpkgs";
    nvfetcher.inputs.flake-compat.follows = "flake-compat";
    nixpkgs-unstable.url = "github:nixos/nixpkgs/nixos-unstable";
    nixos-stable.url = "github:nixos/nixpkgs/nixos-25.05";
  };
  outputs =
    inputs@{
      self,
      nixpkgs,
      nvfetcher,
      flake-parts,
      ...
    }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      systems = [
        "x86_64-linux"
        "aarch64-linux"
      ];
      imports = [
        inputs.flake-parts.flakeModules.easyOverlay
        inputs.devshell.flakeModule
        inputs.treefmt-nix.flakeModule
        ./flake
      ];
      packages = {
        x86_64-linux =
          let
            pkgs = import nixpkgs { system = "x86_64-linux"; };
          in
          {
            userEnvironment = pkgs.buildEnv {
              paths = with pkgs; [
                abuild
                acpi
                ags
                akvcam
                alsa
                alsacontrol
                alvr
                amsynth
                anacrontab
                android-studio
                ansible-bundler
                ant
                anthy
                anubis
                apparmor
                appimagelauncher
                apt-swarm
                archive
                ardour8
                aria2
                arrpc
                arti
                asd
                astro
                astroid
                audacity
                audiovitamins
                audit
                babeld
                bacon
                baloo
                basedpyright
                bash
                bauerbill
                bauh
                bemenu
                berg-cli
                biome
                biometric-auth
                bird
                blacklist-script
                blender
                blendnet
                bluetooth
                bob
                bogofilter
                booster
                btop
                burp
                byobu
                caches-manager
                caddy
                caja
                caja-actions
                calendar
                carbonyl
                cardinal
                cargo
                cava
                cdi
                cg
                clamav
                clight
                clustershell
                cmake
                cmrt
                code
                conda
                configstore
                composer
                connman
                containers
                couchdb
                coursier
                cowrie
                create-next-app-nodejs
                css
                csync2
                cuda
                cvechecker
                datomic
                dbeaver
                dbus-1
                depot_tools
                dhtcluster
                dict
                diffuser
                dillo
                dirsrv
                discord-irc
                discordo
                discover_overlay
                displaycal
                distcc
                dleyna
                docker
                dxvk
                e2scrub
                easyeffects
                editorconfig
                egl
                enscript
                eslint
                f3d
                fakechroot
                fastfetch
                fauxnix
                fcitx
                fcitx5
                fern-wifi-cracker
                ffmpeg
                ffmulticonverter
                fftrate
                fig2ps
                firebuild
                firejail
                fish
                flakehub
                flexiblasrc.d
                flipper
                flutter
                fontconfig
                fonts
                foot
                fop
                foremost
                forgejo
                forgejo-runner
                fpc
                fprintd
                fstab
                fuse
                fuzzel
                fvm
                fwupd
                gai
                gamescope
                ganesha
                gconf
                gdb
                gdnsd
                gh
                ghidra
                ghostty
                gimp
                git
                githooks
                github
                gitlab-container-registry
                glusterfs
                gnunet
                gnuradio
                gnutls
                godot
                goffice
                greetd
                grekllm
                grub.d
                gss
                gsu
                gtk-2
                .0
                gtk-3
                .0
                gtk-4
                .0
                gtk-engines
                gufetch
                gummi
                guvcview2
                hyprland
                icecream
                icegrid
                icmake
                ieamaudioplugins
                imagemagick-7
                imv
                infiniband-diags
                infnoise
                inkscape
                input
                inputplumber
                input-remapper
                inspircd
                intel
                intelpwm
                intel-undervolt
                inwx
                ipmi
                ipp-usb
                ipsec
                ipython
                irker
                irssi
                isns
                iwd
                java-jdk
                jcryptool
                jellyfin
                jflash
                jgit
                jitsi-meet-desktop
                jj
                john
                julia
                jupyter
                limine
                neovim
                nyx
                postfix
                python3
                rage
                rkhunter
                vesktop
                xdg-dbus-proxy
                xdg-desktop-portal
                xdg-desktop-portal-hyprland
                xdg-ninja
                xdg-user-dirs
                xdg-utils
                wine
                wireguard
                zathura
              ];
            };
          };
        aarch64-linux =
          let
            pkgs = import nixpkgs { system = "aarch64-linux"; };
          in
          {
            userEnvironment = pkgs.buildEnv {
              name = "qompass-user-environment";
              paths = with pkgs; [
                git
                neovim
                python311
              ];
            };
          };
      };
    };
}
