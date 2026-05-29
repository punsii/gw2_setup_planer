{ pkgs
, lib
, config
, ...
}:
let
  # Single dir holds the streamlit config (.streamlit/config.toml) and the
  # SQLite DB. Created and chowned by systemd via StateDirectory below.
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
        # DynamicUser: systemd allocates a transient unprivileged user just
        # for this service. StateDirectory creates and chowns
        # /var/lib/gw2-setup-planer for that user; that path is both the
        # working dir AND the default DB location (storage.py's db_path()).
        # CacheDirectory gives `nix run` a writable XDG cache location.
        serviceConfig = {
          DynamicUser = true;
          StateDirectory = "gw2-setup-planer";
          StateDirectoryMode = "0750";
          CacheDirectory = "gw2-setup-planer";
          # nix run resolves its eval cache via $HOME/.cache/nix. Under
          # DynamicUser $HOME defaults to /var/empty (read-only), so point
          # it at the writable CacheDirectory instead. XDG_CACHE_HOME also
          # set for any tool that prefers the XDG path.
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
