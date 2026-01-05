#!/usr/bin/env bash
# CORTEX Desktop - Build Script
# Forces usage of Nix Rust toolchain instead of rustup

set -e

echo "🔧 CORTEX Desktop Build"
echo "======================================"
echo ""

# Check if in Nix environment
if [ -z "$IN_NIX_SHELL" ]; then
    echo "❌ Not in Nix shell!"
    echo "Run: nix develop"
    echo ""
    exit 1
fi

# Verify Rust from Nix
RUST_PATH=$(which rustc)
if [[ "$RUST_PATH" != *"/nix/store/"* ]]; then
    echo "⚠️  WARNING: Using rustup instead of Nix Rust"
    echo "Rust path: $RUST_PATH"
    echo ""
    echo "Temporarily disabling rustup..."
    export PATH=$(echo $PATH | tr ':' '\n' | grep -v rustup | tr '\n' ':')
fi

# Show versions
echo "✓ Rust: $(rustc --version)"
echo "✓ Cargo: $(cargo --version)"
echo "✓ Bun: $(bun --version)"
echo ""

# Build
cd cortex-desktop

echo "🚀 Starting Tauri dev server..."
echo ""

bun run tauri dev
