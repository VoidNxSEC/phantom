{
  description = "🔮 SPECTRE - Sentiment & Pattern Extraction for Contextual Text Research Engine";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          config.allowUnfree = true;
        };

        # ═══════════════════════════════════════════════════════════════
        # PYTHON ENVIRONMENT - NLP & Data Science Stack
        # ═══════════════════════════════════════════════════════════════
        pythonEnv = pkgs.python3.withPackages (ps: with ps; [
          # ── Core Data Science ──
          pandas
          numpy
          scipy
          
          # ── Text Processing ──
          nltk
          regex
          chardet
          
          # ── Visualization ──
          matplotlib
          seaborn
          plotly
          
          # ── ML/Statistics ──
          scikit-learn
          
          # ── Output Formats ──
          jinja2
          pyyaml
          
          # ── CLI/UX ──
          rich
          tqdm
          click
          
          # ── Testing ──
          pytest
          pytest-cov
        ]);

        # ═══════════════════════════════════════════════════════════════
        # SYSTEM TOOLS
        # ═══════════════════════════════════════════════════════════════
        systemTools = with pkgs; [
          # ── Text Processing ──
          jq
          yq-go
          miller
          ripgrep
          fd
          
          # ── Data Viz ──
          gnuplot
          graphviz
          
          # ── Utilities ──
          tree
          bat
          glow  # Markdown renderer
        ];

        # ═══════════════════════════════════════════════════════════════
        # SPECTRE CLI WRAPPER
        # ═══════════════════════════════════════════════════════════════
        spectreCli = pkgs.writeScriptBin "spectre" ''
          #!${pkgs.bash}/bin/bash
          exec ${pythonEnv}/bin/python3 ${./spectre.py} "$@"
        '';

        # ═══════════════════════════════════════════════════════════════
        # QUICK ANALYSIS SCRIPT
        # ═══════════════════════════════════════════════════════════════
        spectreQuick = pkgs.writeScriptBin "spectre-quick" ''
          #!${pkgs.bash}/bin/bash
          # Quick sentiment analysis for a single file or stdin
          
          set -euo pipefail
          
          if [[ $# -eq 0 ]]; then
            echo "Usage: spectre-quick <file.md> or echo 'text' | spectre-quick -"
            exit 1
          fi
          
          INPUT="$1"
          
          ${pythonEnv}/bin/python3 << 'PYEOF'
import sys
import re
import statistics

# Mini sentiment lexicon
LEXICON = {
    'good': 0.5, 'great': 0.7, 'excellent': 0.8, 'amazing': 0.8,
    'bad': -0.5, 'terrible': -0.8, 'poor': -0.6, 'awful': -0.8,
    'innovative': 0.6, 'secure': 0.5, 'vulnerable': -0.7, 'risky': -0.5,
    'bullish': 0.7, 'bearish': -0.7, 'growth': 0.5, 'crash': -0.8,
    'decentralized': 0.4, 'trustless': 0.5, 'hack': -0.8, 'scam': -0.9,
    'adoption': 0.5, 'breakthrough': 0.7, 'failed': -0.6, 'success': 0.6,
}

if len(sys.argv) > 1 and sys.argv[1] != '-':
    with open(sys.argv[1]) as f:
        text = f.read()
else:
    text = sys.stdin.read()

words = re.findall(r'\b\w+\b', text.lower())
scores = [LEXICON.get(w, 0) for w in words]
matched = [w for w in words if w in LEXICON]

if scores:
    compound = sum(scores) / (len(scores) ** 0.5)
    compound = compound / (abs(compound) + 15) ** 0.5 if compound else 0
else:
    compound = 0

label = "POSITIVE" if compound > 0.05 else "NEGATIVE" if compound < -0.05 else "NEUTRAL"

print(f"\033[0;36m📊 Quick Sentiment Analysis\033[0m")
print(f"   Words: {len(words)}")
print(f"   Matched: {len(matched)}")
print(f"   Score: {compound:.4f}")
print(f"   Label: {label}")
if matched:
    print(f"   Terms: {', '.join(set(matched)[:10])}")
PYEOF
        '';

        # ═══════════════════════════════════════════════════════════════
        # TOPIC SCANNER
        # ═══════════════════════════════════════════════════════════════
        spectreScan = pkgs.writeScriptBin "spectre-scan" ''
          #!${pkgs.bash}/bin/bash
          # Scan directory for topic distribution
          
          DIR="''${1:-.}"
          TAXONOMY="''${2:-}"
          
          echo -e "\033[0;35m🔍 SPECTRE Topic Scanner\033[0m"
          echo "========================="
          echo "Directory: $DIR"
          echo ""
          
          if [[ -n "$TAXONOMY" ]] && [[ -f "$TAXONOMY" ]]; then
            echo -e "\033[0;33mUsing taxonomy: $TAXONOMY\033[0m"
            while IFS= read -r term; do
              term_clean=$(echo "$term" | tr '[:upper:]' '[:lower:]' | xargs)
              if [[ -n "$term_clean" ]]; then
                count=$(rg -i -c "$term_clean" "$DIR" --glob "*.md" 2>/dev/null | awk -F: '{sum+=$2} END {print sum+0}')
                if [[ $count -gt 0 ]]; then
                  printf "  %-30s %5d mentions\n" "$term_clean" "$count"
                fi
              fi
            done < "$TAXONOMY" | sort -t$'\t' -k2 -rn | head -30
          else
            echo -e "\033[0;33mTop terms (no taxonomy provided):\033[0m"
            rg -oIN '\b[A-Za-z]{4,}\b' "$DIR" --glob "*.md" 2>/dev/null | \
              tr '[:upper:]' '[:lower:]' | \
              sort | uniq -c | sort -rn | head -30
          fi
        '';

        # ═══════════════════════════════════════════════════════════════
        # CORPUS STATS
        # ═══════════════════════════════════════════════════════════════
        spectreStats = pkgs.writeScriptBin "spectre-stats" ''
          #!${pkgs.bash}/bin/bash
          # Quick corpus statistics
          
          DIR="''${1:-.}"
          
          echo -e "\033[0;35m📊 SPECTRE Corpus Statistics\033[0m"
          echo "=============================="
          
          MD_COUNT=$(find "$DIR" -name "*.md" -type f 2>/dev/null | wc -l)
          TOTAL_LINES=$(find "$DIR" -name "*.md" -type f -exec wc -l {} + 2>/dev/null | tail -1 | awk '{print $1}')
          TOTAL_WORDS=$(find "$DIR" -name "*.md" -type f -exec wc -w {} + 2>/dev/null | tail -1 | awk '{print $1}')
          TOTAL_SIZE=$(find "$DIR" -name "*.md" -type f -exec du -ch {} + 2>/dev/null | tail -1 | awk '{print $1}')
          
          echo "  📁 Directory:    $DIR"
          echo "  📄 MD Files:     $MD_COUNT"
          echo "  📝 Total Lines:  $TOTAL_LINES"
          echo "  📖 Total Words:  $TOTAL_WORDS"
          echo "  💾 Total Size:   $TOTAL_SIZE"
          
          if [[ $MD_COUNT -gt 0 ]]; then
            AVG_WORDS=$((TOTAL_WORDS / MD_COUNT))
            echo "  📊 Avg Words/Doc: $AVG_WORDS"
          fi
          
          echo ""
          echo -e "\033[0;33mLargest files:\033[0m"
          find "$DIR" -name "*.md" -type f -exec wc -w {} + 2>/dev/null | sort -rn | head -5
        '';

        # ═══════════════════════════════════════════════════════════════
        # SENTIMENT HEATMAP GENERATOR
        # ═══════════════════════════════════════════════════════════════
        spectreHeatmap = pkgs.writeScriptBin "spectre-heatmap" ''
          #!${pkgs.bash}/bin/bash
          # Generate ASCII heatmap from sentiment CSV
          
          CSV="$1"
          
          if [[ -z "$CSV" ]] || [[ ! -f "$CSV" ]]; then
            echo "Usage: spectre-heatmap <sentiment_data.csv>"
            exit 1
          fi
          
          ${pythonEnv}/bin/python3 << PYEOF
import csv
import sys

def color_score(score):
    score = float(score)
    if score >= 0.5: return '\033[0;32m██\033[0m'  # Green
    elif score >= 0.2: return '\033[0;32m▓▓\033[0m'
    elif score >= 0.05: return '\033[0;33m▒▒\033[0m'  # Yellow
    elif score >= -0.05: return '\033[0;37m░░\033[0m'  # Gray
    elif score >= -0.2: return '\033[0;33m▒▒\033[0m'
    elif score >= -0.5: return '\033[0;31m▓▓\033[0m'  # Red
    else: return '\033[0;31m██\033[0m'

print("\033[0;35m📊 Sentiment Heatmap\033[0m")
print("Legend: \033[0;32m██\033[0m very positive  \033[0;33m▒▒\033[0m neutral  \033[0;31m██\033[0m very negative")
print("")
print(f"{'Document':<30} {'Overall':^8} {'Tech':^8} {'Market':^8} {'Comm':^8} {'Innov':^8} {'Risk':^8}")
print("-" * 90)

with open("$CSV") as f:
    reader = csv.DictReader(f)
    for row in reader:
        name = row['filename'][:28] + '..' if len(row['filename']) > 30 else row['filename']
        print(f"{name:<30} ", end="")
        for dim in ['overall', 'technical', 'market', 'community', 'innovation', 'risk']:
            print(f"  {color_score(row.get(dim, 0))}  ", end="")
        print()
PYEOF
        '';

      in
      {
        # ═══════════════════════════════════════════════════════════════
        # DEVELOPMENT SHELL
        # ═══════════════════════════════════════════════════════════════
        devShells.default = pkgs.mkShell {
          name = "spectre-nlp";
          
          buildInputs = [
            pythonEnv
            spectreCli
            spectreQuick
            spectreScan
            spectreStats
            spectreHeatmap
          ] ++ systemTools;
          
          shellHook = ''
            export SPECTRE_VERSION="${VERSION}"
            export PYTHONDONTWRITEBYTECODE=1
            
            # Create work directories
            mkdir -p .spectre/{input,output,taxonomy}
            
            # Copy taxonomy if exists
            if [[ -f taxonomy.txt ]] && [[ ! -f .spectre/taxonomy/blockchain.txt ]]; then
              cp taxonomy.txt .spectre/taxonomy/blockchain.txt 2>/dev/null || true
            fi
            
            echo -e "\033[0;35m"
            cat << 'BANNER'
╔══════════════════════════════════════════════════════════════════════════════════╗
║  ███████╗██████╗ ███████╗ ██████╗████████╗██████╗ ███████╗                       ║
║  ██╔════╝██╔══██╗██╔════╝██╔════╝╚══██╔══╝██╔══██╗██╔════╝                       ║
║  ███████╗██████╔╝█████╗  ██║        ██║   ██████╔╝█████╗                         ║
║  ╚════██║██╔═══╝ ██╔══╝  ██║        ██║   ██╔══██╗██╔══╝                         ║
║  ███████║██║     ███████╗╚██████╗   ██║   ██║  ██║███████╗                       ║
║  ╚══════╝╚═╝     ╚══════╝ ╚═════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝                       ║
║  Sentiment & Pattern Extraction for Contextual Text Research Engine              ║
╚══════════════════════════════════════════════════════════════════════════════════╝
BANNER
            echo -e "\033[0m"
            
            echo -e "\033[0;36m🔮 SPECTRE Environment Loaded\033[0m"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo ""
            echo -e "\033[0;33m📦 Core Commands:\033[0m"
            echo "  spectre -i <input> -o <output> [-t taxonomy.txt]"
            echo "                               Full corpus analysis"
            echo ""
            echo -e "\033[0;33m🔧 Quick Tools:\033[0m"
            echo "  spectre-quick <file.md>      Quick sentiment for single file"
            echo "  spectre-scan <dir> [tax]     Topic distribution scan"
            echo "  spectre-stats <dir>          Corpus statistics"
            echo "  spectre-heatmap <data.csv>   ASCII sentiment heatmap"
            echo ""
            echo -e "\033[0;33m📁 Directory Structure:\033[0m"
            echo "  .spectre/input/              Place .md files here"
            echo "  .spectre/output/             Analysis results"
            echo "  .spectre/taxonomy/           Domain taxonomies"
            echo ""
            echo -e "\033[0;33m🚀 Quick Start:\033[0m"
            echo "  1. cp -r /path/to/markdown/docs .spectre/input/"
            echo "  2. spectre -i .spectre/input -o .spectre/output -t taxonomy.txt -v"
            echo "  3. glow .spectre/output/reports/summary_report_*.md"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
          '';
        };
        
        # ═══════════════════════════════════════════════════════════════
        # PACKAGES
        # ═══════════════════════════════════════════════════════════════
        packages = {
          default = spectreCli;
          spectre = spectreCli;
          spectre-quick = spectreQuick;
          spectre-scan = spectreScan;
          spectre-stats = spectreStats;
          spectre-heatmap = spectreHeatmap;
        };
        
        # ═══════════════════════════════════════════════════════════════
        # APPS
        # ═══════════════════════════════════════════════════════════════
        apps = {
          default = {
            type = "app";
            program = "${spectreCli}/bin/spectre";
          };
        };
      }
    );
}
