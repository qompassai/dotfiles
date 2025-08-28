# /qompassai/dotfiles/.config/nixpkgs/config.nix
{
  allowUnfree = true;
  enableParallelBuildingByDefault = true;
  allowAliases = true;
  replaceStdenv = {pkgs}: pkgs.impureUseNativeOptimizations pkgs.stdenv;
  permittedInsecurePackages = [
  ];

  packageOverrides = pkgs:
    with pkgs; rec {
      hpc-env = pkgs.buildEnv {
        name = "hpc-development";
        paths = [
          gcc
          gfortran
          openmpi
          blas
          lapack
          fftw
          gsl
          git
          cmake
          ninja
        ];
        pathsToLink = ["/bin" "/share" "/include" "/lib"];
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
        pathsToLink = ["/bin" "/share"];
      };
    };
}
