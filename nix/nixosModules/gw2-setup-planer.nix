{ pkgs
, lib
, config
, ...
}:
let
  WorkingDirectory = "/srv/gw2_setup_planer";
  StreamlitConfig = pkgs.writeText "config.toml" ''
    [theme]
    base="dark"
    primaryColor="#AB00AB"

    [server]
    port = 14444

    [client]
    showErrorDetails = false
  '';
in
{

  options = {
    gw2-setup-planer = {
      enable = lib.mkEnableOption "enables gw2 setup planer streamlit app";
      caddy = {
        enable = lib.mkEnableOption ''
          Enable the caddy reverse proxy for this service.
          Be sure to also set your email in caddy.service.globalConfig.
          If disabled the app is only hosted on localhost:14444.
        '';
        domainName = lib.mkOption {
          default = "";
          example = "my-domain.net";
          description = "Used as the virtualHosts for the caddy reverse proxy.";
          type = lib.types.str;
        };
      };
    };
  };

  config = lib.mkIf config.gw2-setup-planer.enable {
    systemd.timers."gw2-setup-planer" = {
      wantedBy = [ "timers.target" ];
      timerConfig = {
        OnCalendar = "*-*-* 03:30:00";
        RandomizedDelaySec = "1800";
        Persistent = "true";
        Unit = "gw2-setup-planer-restart";
      };
    };
    systemd.services = {
      "gw2-setup-planer-restart" = {
        description = "Service for restarting the gw2 setup planer streamlit app";
        script = ''
          ${pkgs.systemd}/bin/systemctl restart gw2-setup-planer.service
        '';
        serviceConfig = {
          Type = "oneshot";
        };
      };
      "gw2-setup-planer" = {
        description = "Service for hosting the gw2 setup planer streamlit app";
        script = ''
          ${pkgs.coreutils}/bin/mkdir -vp ${WorkingDirectory}/.streamlit
          cp -v ${StreamlitConfig} ${WorkingDirectory}/.streamlit/${StreamlitConfig.name}
          cd ${WorkingDirectory}
          ${pkgs.nix}/bin/nix run "github:punsii/gw2_setup_planer/master"
        '';
        wantedBy = [ "multi-user.target" ];
        requires = [ "network-online.target" ];
        after = [ "network-online.target" ];
        # StateDirectory creates and chowns /var/lib/gw2-setup-planer for the
        # service, where storage.py drops its default SQLite DB file.
        serviceConfig = {
          StateDirectory = "gw2-setup-planer";
          StateDirectoryMode = "0750";
        };
      };
    };

    services.caddy =
      let
        domain = config.gw2-setup-planer.caddy.domainName;
      in
      lib.mkIf config.gw2-setup-planer.caddy.enable {
        enable = true;
        virtualHosts.${domain}.extraConfig = ''
          encode gzip
          reverse_proxy 127.0.0.1:14444
        '';
      };
    networking.firewall.allowedTCPPorts = lib.mkIf config.gw2-setup-planer.caddy.enable [
      80
      443
    ];
  };
}
