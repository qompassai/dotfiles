# /qompassai/dotfiles/.config/nixpkgs/config.nix
{ pkgs, ... }:
{
  allowUnfree = true;
  enableParallelBuildingByDefault = true;
  allowAliases = true;
  replaceStdenv = { pkgs }: pkgs.impureUseNativeOptimizations pkgs.stdenv;
  packageOverrides =
    pkgs: with pkgs; rec {
      hpc-env = pkgs.buildEnv {
        name = "hpc-development";
        paths = [
          bison
          blas
          cmake
          fftw
          gcc
          gfortran
          git
          gsl
          openmpi
          lapack
          ninja
        ];
        pathsToLink = [
          "/bin"
          "/share"
          "/include"
          "/lib"
        ];
      };
      quantum-env = pkgs.buildEnv {
        name = "quantum-computing";
        paths = [
          python3
          python3Packages.numpy
          python3Packages.scipy
          python3Packages.matplotlib
          python3Packages.jupyter
        ];
        pathsToLink = [
          "/bin"
          "/share"
        ];
      };
    };
}
