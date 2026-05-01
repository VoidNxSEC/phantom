#!/usr/bin/env bash
set -euo pipefail

echo "🧠 CEREBRO - RAG Knowledge System Test"
echo "======================================="
echo ""

# Check if running in Nix environment
if [ -z "${IN_NIX_SHELL:-}" ]; then
    echo "Entering Nix development environment..."
    nix develop -c "$0" "$@"
    exit $?
fi

cd "$(dirname "$0")"

echo "📚 Testing Knowledge Loader..."
python -m phantom.cerebro.knowledge_loader

echo ""
echo "================================="
echo ""

echo "🔍 Testing RAG Engine..."
python -m phantom.cerebro.rag_engine

echo ""
echo "================================="
echo ""

echo "✅ Tests complete!"
echo ""
echo "Next: Start Phantom API and test /judge endpoint"
echo "  ./start_api.sh"
