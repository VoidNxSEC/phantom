#!/usr/bin/env bash
set -e

echo "🚀 Starting Stack Validation..."

# 1. Nix Flake Checks
echo "📦 Checking Nix Flake configuration and inputs..."
if nix flake check --show-trace; then
    echo "✅ Nix Flake Check Passed"
else
    echo "❌ Nix Flake Check Failed"
    exit 1
fi

# 2. Python Build
echo "🐍 Building Phantom (Python)..."
if nix build .#phantom --print-build-logs; then
    echo "✅ Python Build Passed"
else
    echo "❌ Python Build Failed"
    exit 1
fi

echo "🎉 Stack Validation Complete! All systems go."
