{
  description = "This is a python script that downloads Arch Linux packages (Official/Chaotic AUR) and converts to an AppImage executable";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs-22.05";
    flake-utils.url = "github:numtide/flake-utils";

    # This section will allow us to create a python environment
    # with specific predefined python packages from PyPi
    pypi-deps-db = {
      url = "github:DavHau/pypi-deps-db";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.mach-nix.follows = "mach-nix";
    };
    mach-nix = {
      url = "github:DavHau/mach-nix/3.3.0";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.flake-utils.follows = "flake-utils";
      inputs.pypi-deps-db.follows = "pypi-deps-db";
    };
  };

  outputs = { self, nixpkgs, flake-utils, mach-nix, ... }@attr:
  flake-utils.lib.eachDefaultSystem (system:
    let
      pkgs = import nixpkgs { inherit system; };

      # prepare mach-nix for usage
      mach = mach-nix.lib.${system};
      
      # create a custom python environment
      myPython = mach.mkPython {
        # specify the base version of python you with to use
        python = "python39";

        requirements = pkgs.readFile ./requirements.txt;
      };
    in {
      devShell = pkgs.mkShell {
        nativeBuildInputs = [
          myPython
        ];
      };
    }
  );
}
