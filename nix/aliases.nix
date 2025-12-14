# Shell aliases for Phantom integration with NixOS
# Import this in your NixOS modules/shell/aliases/
{ config, lib, pkgs, ... }:

let
  cfg = config.programs.phantom-aliases;
in {
  options.programs.phantom-aliases = {
    enable = lib.mkEnableOption "Phantom shell aliases";
  };

  config = lib.mkIf cfg.enable {
    environment.shellAliases = {
      # ═══════════════════════════════════════════════════════════════
      # PHANTOM CORE COMMANDS
      # ═══════════════════════════════════════════════════════════════
      
      # Main CLI
      phantom = "nix run github:kernelcore/phantom --";
      ph = "phantom";
      
      # Document processing
      px = "phantom extract";          # Extract insights
      pa = "phantom analyze";          # Full analysis
      pc = "phantom classify";         # Classify files
      ps = "phantom scan";             # Scan for sensitive data
      
      # ═══════════════════════════════════════════════════════════════
      # RAG PIPELINE
      # ═══════════════════════════════════════════════════════════════
      
      prag = "phantom rag query";       # RAG query
      pingest = "phantom rag ingest";   # Ingest documents
      psearch = "phantom rag search";   # Semantic search
      
      # ═══════════════════════════════════════════════════════════════
      # TOOLS
      # ═══════════════════════════════════════════════════════════════
      
      pvram = "phantom tools vram";     # VRAM calculator
      pprompt = "phantom tools prompt"; # Prompt workbench
      paudit = "phantom tools audit";   # Project auditor
      
      # ═══════════════════════════════════════════════════════════════
      # API SERVER
      # ═══════════════════════════════════════════════════════════════
      
      papi = "phantom api serve";       # Start API server
      papi-dev = "phantom api serve --reload"; # Dev mode
      
      # ═══════════════════════════════════════════════════════════════
      # QUICK RECIPES
      # ═══════════════════════════════════════════════════════════════
      
      # Process directory of markdown files
      phantom-process = ''
        phantom extract \
          --input . \
          --output ./insights.jsonl \
          --format jsonl \
          --verbose
      '';
      
      # Quick RAG setup
      phantom-rag-setup = ''
        phantom rag ingest --dir ./docs && \
        echo "✅ RAG index created"
      '';
    };
  };
}
