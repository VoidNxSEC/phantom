{ config, lib, pkgs, ... }:

let
  cfg = config.services.phantom;
in {
  options.services.phantom = {
    enable = lib.mkEnableOption "Phantom AI toolkit";

    package = lib.mkOption {
      type = lib.types.package;
      default = pkgs.phantom or (throw "phantom package not in pkgs");
      description = "The phantom package to use";
    };

    api = {
      enable = lib.mkEnableOption "Phantom REST API server";
      
      port = lib.mkOption {
        type = lib.types.port;
        default = 8000;
        description = "Port for the API server";
      };

      host = lib.mkOption {
        type = lib.types.str;
        default = "127.0.0.1";
        description = "Host to bind the API server";
      };
    };

    providers = {
      llamacpp = {
        url = lib.mkOption {
          type = lib.types.str;
          default = "http://localhost:8080";
          description = "llama.cpp TURBO server URL";
        };
      };
    };

    vectorDb = {
      backend = lib.mkOption {
        type = lib.types.enum [ "faiss" "chromadb" ];
        default = "faiss";
        description = "Vector database backend";
      };

      path = lib.mkOption {
        type = lib.types.path;
        default = "/var/lib/phantom/vectors";
        description = "Path to store vector indices";
      };
    };
  };

  config = lib.mkIf cfg.enable {
    # Add phantom to system packages
    environment.systemPackages = [ cfg.package ];

    # Create state directory
    systemd.tmpfiles.rules = [
      "d /var/lib/phantom 0755 root root -"
      "d ${cfg.vectorDb.path} 0755 root root -"
    ];

    # Environment variables for providers
    environment.sessionVariables = {
      LLAMACPP_URL = cfg.providers.llamacpp.url;
      PHANTOM_VECTOR_PATH = cfg.vectorDb.path;
    };

    # API service (if enabled)
    systemd.services.phantom-api = lib.mkIf cfg.api.enable {
      description = "Phantom AI API Server";
      after = [ "network.target" ];
      wantedBy = [ "multi-user.target" ];

      environment = {
        LLAMACPP_URL = cfg.providers.llamacpp.url;
        PHANTOM_VECTOR_PATH = cfg.vectorDb.path;
      };

      serviceConfig = {
        Type = "simple";
        ExecStart = "${cfg.package}/bin/phantom-api --host ${cfg.api.host} --port ${toString cfg.api.port}";
        Restart = "on-failure";
        RestartSec = 5;
        
        # Security hardening
        DynamicUser = true;
        StateDirectory = "phantom";
        PrivateTmp = true;
        ProtectSystem = "strict";
        ProtectHome = true;
        NoNewPrivileges = true;
      };
    };
  };
}
