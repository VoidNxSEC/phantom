#!/usr/bin/env bash
set -euo pipefail

echo "🔮 Starting Phantom API..."

# Check if running in Nix environment
if [ -z "${IN_NIX_SHELL:-}" ]; then
    echo "Entering Nix development environment..."
    nix develop -c "$0" "$@"
    exit $?
fi

# We're now in nix shell
cd "$(dirname "$0")"

echo "Starting FastAPI server on http://localhost:8081"
echo ""
echo "Endpoints available:"
echo "  GET  /health     - Health check"
echo "  POST /process    - CORTEX document processing"
echo "  POST /analyze    - SPECTRE analysis"
echo "  POST /judge      - AI-OS-Agent bundle judgment"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python -m phantom.api.cortex_api
