{
  description = "setup planner for gw2 gvg squad composition";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    treefmt-nix = {
      url = "github:numtide/treefmt-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, treefmt-nix }:

    let
      system = "x86_64-linux";
      pkgs = import nixpkgs {
        inherit system;
      };
      treefmtEval = treefmt-nix.lib.evalModule pkgs
        {
          # Used to find the project root
          projectRootFile = "flake.nix";

          programs = {
            black.enable = true;
            isort.enable = true;
            prettier.enable = true;
            nixpkgs-fmt.enable = true;
          };
        };

      src = pkgs.runCommandLocal "gw2-setup-planer-sources" { } ''
        cp -vr ${pkgs.lib.cleanSource ./.} $out
      '';

      pythonEnv = pkgs.python3.withPackages (
        ps: with ps; [
          streamlit
        ]
      );

      prodApp = pkgs.writeShellApplication {
        name = "streamlitRun";
        runtimeInputs = [ pythonEnv ];
        text = "${pythonEnv}/bin/python3 -m streamlit run ${src}/app.py";
      };

      devApp = pkgs.writeShellApplication {
        name = "streamlitRun";
        runtimeInputs = [ pythonEnv ];
        text = "${pythonEnv}/bin/python3 -m streamlit run app.py";
      };
    in
    {
      apps.${system} = rec {
        default = prod;
        prod = {
          type = "app";
          program = "${prodApp}/bin/streamlitRun";
        };
        dev = {
          type = "app";
          program = "${devApp}/bin/streamlitRun";
        };
      };

      devShells.${system} = {
        default = pkgs.mkShell {
          buildInputs = with pkgs; [
            treefmtEval.config.build.wrapper

            pythonEnv

            # tools
            black
            pylint
            pyright
            ruff
          ];
        };
      };

      nixosModules = rec {
        gw2-setup-planer = ./nix/nixosModules/gw2-setup-planer.nix;
        default = gw2-setup-planer;
      };

      formatter.${system} = treefmtEval.config.build.wrapper;
    };
}
