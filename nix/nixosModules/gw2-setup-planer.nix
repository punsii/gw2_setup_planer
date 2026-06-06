{ pkgs
, lib
, config
, ...
}:
let
  WorkingDirectory = "/var/lib/gw2-setup-planer";
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
    users.users.gw2-setup-planer = {
      isSystemUser = true;
      group = "gw2-setup-planer";
      description = "gw2-setup-planer service user";
    };
    users.groups.gw2-setup-planer = { };

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
          ${pkgs.nix}/bin/nix run "github:punsii/gw2_setup_planer/main"
        '';
        wantedBy = [ "multi-user.target" ];
        requires = [ "network-online.target" ];
        after = [ "network-online.target" ];
        serviceConfig = {
          User = "gw2-setup-planer";
          Group = "gw2-setup-planer";
          StateDirectory = "gw2-setup-planer";
          StateDirectoryMode = "0750";
          CacheDirectory = "gw2-setup-planer";

          NoNewPrivileges = true;
          ProtectSystem = "strict";
          ProtectHome = true;
          PrivateTmp = true;

          Environment = [
            "HOME=/var/cache/gw2-setup-planer"
            "XDG_CACHE_HOME=/var/cache/gw2-setup-planer"
          ];
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
