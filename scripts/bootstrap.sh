#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# PHANTOM CLASSIFIER - Bootstrap & Demo Script
# ═══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[0;33m'
MAGENTA='\033[0;35m'
NC='\033[0m'

echo -e "${MAGENTA}"
cat << 'BANNER'
╔══════════════════════════════════════════════════════════════════════════════╗
║  🔮 PHANTOM CLASSIFIER - Bootstrap Script                                     ║
╚══════════════════════════════════════════════════════════════════════════════╝
BANNER
echo -e "${NC}"

# ═══════════════════════════════════════════════════════════════════════════════
# CREATE DEMO DATA
# ═══════════════════════════════════════════════════════════════════════════════

create_demo_data() {
    echo -e "${CYAN}📁 Creating demo data structure...${NC}"
    
    DEMO_DIR="${1:-./demo_input}"
    mkdir -p "$DEMO_DIR"/{documents,code,configs,images,data,misc}
    
    # Documents
    echo "# Secret Project Report Q4 2024

## Executive Summary
This document contains confidential information about Project PHANTOM.

Contact: john.doe@secretcorp.com
Phone: 555-123-4567

## Budget
Total: $1,250,000
" > "$DEMO_DIR/documents/project_report.md"

    echo "Meeting notes from 2024-01-15
Attendees: alice@company.com, bob@company.com
Password for shared drive: S3cr3tP@ss123
API Key: sk_live_4eC39HqLyjWDarjtT1zdp7dc
" > "$DEMO_DIR/documents/meeting_notes.txt"

    # Code files
    cat > "$DEMO_DIR/code/config_loader.py" << 'PYEOF'
#!/usr/bin/env python3
"""Configuration loader with secrets."""

import os

# WARNING: These are dummy credentials for demo
DATABASE_URL = "postgres://admin:password123@db.internal.com:5432/prod"
AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
API_ENDPOINT = "https://api.secretservice.com/v2"

def load_config():
    return {
        "db": DATABASE_URL,
        "aws_key": AWS_ACCESS_KEY,
        "email_admin": "admin@internal.corp",
    }
PYEOF

    cat > "$DEMO_DIR/code/utils.rs" << 'RSEOF'
//! Utility functions for PHANTOM
use std::collections::HashMap;

/// Hash a string with custom salt
pub fn hash_with_salt(input: &str, salt: &str) -> String {
    // Implementation here
    format!("{}-{}", input, salt)
}

pub fn process_data(data: &[u8]) -> Result<Vec<u8>, String> {
    Ok(data.to_vec())
}
RSEOF

    cat > "$DEMO_DIR/code/pipeline.nix" << 'NIXEOF'
{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    python3
    ripgrep
    jq
  ];
  
  shellHook = ''
    echo "Pipeline environment loaded"
  '';
}
NIXEOF

    # Config files
    cat > "$DEMO_DIR/configs/app.env" << 'ENVEOF'
# Application Configuration
DATABASE_HOST=db.production.internal
DATABASE_USER=app_user
DATABASE_PASSWORD=Pr0duct10n_P@ss!
REDIS_URL=redis://cache.internal:6379
JWT_SECRET=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.example
STRIPE_API_KEY=sk_live_xxxxxxxxxxxxxxxxxxxxxxxxx
ENVEOF

    cat > "$DEMO_DIR/configs/nginx.conf" << 'CONFEOF'
server {
    listen 80;
    server_name api.example.com;
    
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header X-API-Key $http_x_api_key;
    }
}
CONFEOF

    # Data files
    cat > "$DEMO_DIR/data/users.json" << 'JSONEOF'
{
  "users": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john.doe@example.com",
      "phone": "555-123-4567",
      "ssn": "123-45-6789",
      "credit_card": "4532-1234-5678-9012"
    },
    {
      "id": 2,
      "name": "Jane Smith",
      "email": "jane.smith@example.com",
      "cpf": "123.456.789-00"
    }
  ]
}
JSONEOF

    cat > "$DEMO_DIR/data/metrics.csv" << 'CSVEOF'
timestamp,metric,value,host
2024-01-15T10:00:00Z,cpu_usage,45.2,server-01.internal.net
2024-01-15T10:00:00Z,memory_usage,78.5,server-01.internal.net
2024-01-15T10:01:00Z,cpu_usage,52.1,server-02.internal.net
CSVEOF

    # Misc files
    echo "Random log output from process PID 12345
Error connecting to 192.168.1.100:5432
Connection string: mongodb://user:pass@mongo.internal:27017/db
[2024-01-15 10:30:00] WARNING: Auth failed for user@domain.com
" > "$DEMO_DIR/misc/app.log"

    # Create a fake "sensitive" key file
    cat > "$DEMO_DIR/configs/private.key" << 'KEYEOF'
-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEA0Z3VS5JJcds3xfn/ygWyF8PbnGy0AHB7MmFzXEXHbPaGIsxn
DEMO_PRIVATE_KEY_FOR_TESTING_ONLY_NOT_REAL
Do not use this key for anything - it is not a real private key
This is just demo data for the PHANTOM classifier
-----END RSA PRIVATE KEY-----
KEYEOF

    # Create some binary-ish files (small)
    echo -e '\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR' > "$DEMO_DIR/images/fake_image.png"
    echo -e '%PDF-1.4 fake pdf content' > "$DEMO_DIR/documents/fake_doc.pdf"
    
    echo -e "${GREEN}✓ Demo data created in: $DEMO_DIR${NC}"
    
    # Show structure
    echo -e "\n${CYAN}📊 Structure:${NC}"
    if command -v tree &>/dev/null; then
        tree "$DEMO_DIR" --noreport
    else
        find "$DEMO_DIR" -type f | sort
    fi
}

# ═══════════════════════════════════════════════════════════════════════════════
# RUN DEMO
# ═══════════════════════════════════════════════════════════════════════════════

run_demo() {
    echo -e "\n${CYAN}🚀 Running PHANTOM classification on demo data...${NC}\n"
    
    INPUT_DIR="${1:-./demo_input}"
    OUTPUT_DIR="${2:-./demo_output}"
    
    if [[ ! -d "$INPUT_DIR" ]]; then
        echo -e "${YELLOW}Creating demo data first...${NC}"
        create_demo_data "$INPUT_DIR"
    fi
    
    # Check if phantom command exists
    if command -v phantom &>/dev/null; then
        phantom -i "$INPUT_DIR" -o "$OUTPUT_DIR" -v
    else
        echo -e "${YELLOW}⚠ 'phantom' command not found. Enter nix develop shell first:${NC}"
        echo "  nix develop"
        echo "  ./bootstrap.sh demo"
        return 1
    fi
    
    echo -e "\n${GREEN}✓ Demo complete!${NC}"
    echo -e "\n${CYAN}📊 Results:${NC}"
    
    if [[ -d "$OUTPUT_DIR" ]]; then
        echo -e "\n${MAGENTA}Classification structure:${NC}"
        ls -la "$OUTPUT_DIR"/ 2>/dev/null | grep -E "^d" | awk '{print "  📁 " $NF}'
        
        echo -e "\n${MAGENTA}File counts per category:${NC}"
        for dir in "$OUTPUT_DIR"/*/; do
            if [[ -d "$dir" ]] && [[ "$(basename "$dir")" != ".phantom" ]]; then
                count=$(find "$dir" -maxdepth 1 -type f 2>/dev/null | wc -l)
                echo "  $(basename "$dir"): $count files"
            fi
        done
        
        echo -e "\n${MAGENTA}Latest report:${NC}"
        REPORT=$(ls -t "$OUTPUT_DIR"/.phantom/reports/*.json 2>/dev/null | head -1)
        if [[ -n "$REPORT" ]]; then
            echo "  $REPORT"
            echo -e "\n${CYAN}Summary:${NC}"
            jq -r '.statistics | "  Processed: \(.processed)\n  Failed: \(.failed)\n  Success Rate: \(.success_rate)\n  Duration: \(.duration_seconds)s"' "$REPORT" 2>/dev/null || true
        fi
    fi
}

# ═══════════════════════════════════════════════════════════════════════════════
# SCAN FOR SENSITIVE DATA
# ═══════════════════════════════════════════════════════════════════════════════

scan_sensitive() {
    DIR="${1:-.}"
    
    echo -e "${MAGENTA}🔍 PHANTOM SENSITIVE DATA SCANNER${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "Target: ${CYAN}$DIR${NC}\n"
    
    # Email patterns
    echo -e "${YELLOW}📧 Email Addresses:${NC}"
    rg -oIN '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}' "$DIR" 2>/dev/null | head -10 || echo "  None found"
    
    # IP addresses
    echo -e "\n${YELLOW}🌐 IP Addresses:${NC}"
    rg -oIN '\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b' "$DIR" 2>/dev/null | head -10 || echo "  None found"
    
    # Potential passwords/secrets
    echo -e "\n${YELLOW}🔑 Potential Credentials:${NC}"
    rg -iIN '(password|passwd|pwd|secret|token|api[_-]?key)\s*[=:]\s*["\x27]?[^\s"\x27]+' "$DIR" 2>/dev/null | head -10 || echo "  None found"
    
    # AWS Keys
    echo -e "\n${YELLOW}☁️ AWS Access Keys:${NC}"
    rg -oIN 'AKIA[0-9A-Z]{16}' "$DIR" 2>/dev/null | head -5 || echo "  None found"
    
    # Private keys
    echo -e "\n${YELLOW}🔐 Private Keys:${NC}"
    rg -lIN '-----BEGIN.*PRIVATE KEY-----' "$DIR" 2>/dev/null || echo "  None found"
    
    # Connection strings
    echo -e "\n${YELLOW}💾 Database Connection Strings:${NC}"
    rg -oIN '(mysql|postgres|mongodb|redis)://[^\s]+' "$DIR" 2>/dev/null | head -5 || echo "  None found"
    
    # Brazilian PII
    echo -e "\n${YELLOW}🇧🇷 Brazilian PII (CPF):${NC}"
    rg -oIN '\b[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2}\b' "$DIR" 2>/dev/null | head -5 || echo "  None found"
    
    echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✓ Scan complete${NC}"
}

# ═══════════════════════════════════════════════════════════════════════════════
# CLEANUP
# ═══════════════════════════════════════════════════════════════════════════════

cleanup() {
    echo -e "${YELLOW}🧹 Cleaning up demo files...${NC}"
    rm -rf ./demo_input ./demo_output 2>/dev/null || true
    echo -e "${GREEN}✓ Cleanup complete${NC}"
}

# ═══════════════════════════════════════════════════════════════════════════════
# HELP
# ═══════════════════════════════════════════════════════════════════════════════

show_help() {
    cat << HELP
${CYAN}PHANTOM CLASSIFIER - Bootstrap Script${NC}

${YELLOW}Usage:${NC}
  ./bootstrap.sh <command> [args]

${YELLOW}Commands:${NC}
  create [dir]     Create demo data in specified directory (default: ./demo_input)
  demo [in] [out]  Create demo data and run classification
  scan [dir]       Scan directory for sensitive data patterns
  clean            Remove demo directories
  help             Show this help message

${YELLOW}Examples:${NC}
  ./bootstrap.sh create               # Create demo data
  ./bootstrap.sh demo                 # Full demo run
  ./bootstrap.sh scan /path/to/data   # Scan for sensitive data
  ./bootstrap.sh clean                # Cleanup

${YELLOW}Quick Start:${NC}
  1. nix develop                      # Enter environment
  2. ./bootstrap.sh demo              # Run demo
  3. phantom-report ./demo_output     # View report
HELP
}

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

main() {
    case "${1:-help}" in
        create)
            create_demo_data "${2:-./demo_input}"
            ;;
        demo)
            run_demo "${2:-./demo_input}" "${3:-./demo_output}"
            ;;
        scan)
            scan_sensitive "${2:-.}"
            ;;
        clean)
            cleanup
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo -e "${YELLOW}Unknown command: $1${NC}"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
