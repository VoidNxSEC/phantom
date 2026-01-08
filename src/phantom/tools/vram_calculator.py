#!/usr/bin/env python3
"""
VRAM Calculator - Calcula requisitos de VRAM para modelos LLM

Usage:
  python vram_calculator.py --model-size 30 --quantization Q4_K_M --context-size 4096 --gpu-vram 24
  python vram_calculator.py --interactive
"""

import argparse
import sys
from dataclasses import dataclass

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

QUANTIZATION_FACTORS = {
    "Q2_K": 0.31,
    "Q3_K_S": 0.38,
    "Q3_K_M": 0.44,
    "Q3_K_L": 0.47,
    "Q4_0": 0.50,
    "Q4_K_S": 0.53,
    "Q4_K_M": 0.56,
    "Q4_K_L": 0.59,
    "Q5_0": 0.63,
    "Q5_K_S": 0.66,
    "Q5_K_M": 0.69,
    "Q5_K_L": 0.72,
    "Q6_K": 0.75,
    "Q8_0": 1.00,
    "FP16": 2.00,
    "FP32": 4.00,
}

# Estimativas para modelos comuns (layers, hidden_dim)
MODEL_SPECS = {
    7: {"layers": 32, "hidden_dim": 4096},
    13: {"layers": 40, "hidden_dim": 5120},
    30: {"layers": 60, "hidden_dim": 5120},  # Qwen-Coder-30B
    34: {"layers": 48, "hidden_dim": 6656},  # Yi-34B
    70: {"layers": 80, "hidden_dim": 8192},  # Llama-70B
}

OVERHEAD_GB = 0.5  # llama.cpp overhead


# ═══════════════════════════════════════════════════════════════
# CALCULATOR
# ═══════════════════════════════════════════════════════════════


@dataclass
class VRAMBreakdown:
    """VRAM usage breakdown"""

    model_gb: float
    kv_cache_gb: float
    overhead_gb: float
    batch_gb: float

    @property
    def total_gb(self) -> float:
        return self.model_gb + self.kv_cache_gb + self.overhead_gb + self.batch_gb

    def format_report(self, gpu_vram: float | None = None) -> str:
        """Format detailed report"""
        lines = []
        lines.append("╔═══════════════════════════════════════════════╗")
        lines.append("║  VRAM CALCULATOR - Breakdown                  ║")
        lines.append("╚═══════════════════════════════════════════════╝")
        lines.append("")
        lines.append("📊 VRAM Usage:")
        lines.append(f"  Model:        {self.model_gb:>6.2f} GB")
        lines.append(f"  KV Cache:     {self.kv_cache_gb:>6.2f} GB")
        lines.append(f"  Overhead:     {self.overhead_gb:>6.2f} GB")
        lines.append(f"  Batch:        {self.batch_gb:>6.2f} GB")
        lines.append("  " + "─" * 20)
        lines.append(f"  TOTAL:        {self.total_gb:>6.2f} GB")

        if gpu_vram:
            lines.append("")
            lines.append("🎮 GPU Information:")
            lines.append(f"  GPU VRAM:     {gpu_vram:>6.2f} GB")
            free = gpu_vram - self.total_gb
            lines.append(f"  Free:         {free:>6.2f} GB")

            # Status
            status_color = {
                "critical": "🔴",
                "warning": "🟡",
                "ok": "🟢",
            }

            if free < 1.0:
                status = "critical"
                msg = "CRITICAL - Not enough VRAM!"
            elif free < 2.0:
                status = "warning"
                msg = "WARNING - Very tight on VRAM"
            else:
                status = "ok"
                msg = "OK - Safe to run"

            lines.append(f"  Status:       {status_color[status]} {msg}")

            # Recommendations
            if free < 2.0:
                lines.append("")
                lines.append("💡 Recommendations:")
                if free < 0:
                    lines.append("  ❌ Model won't fit! Consider:")
                    lines.append("     • Lower quantization (Q4→Q3→Q2)")
                    lines.append("     • Smaller context size")
                    lines.append("     • CPU offloading (--n-gpu-layers)")
                    lines.append("     • Smaller model size")
                else:
                    lines.append("  ⚠️  Very tight! Consider:")
                    lines.append("     • Reducing context size")
                    lines.append("     • Lower quantization for safety")

        return "\n".join(lines)


def calculate_vram(
    model_size_b: float, quantization: str, context_size: int, batch_size: int = 1
) -> VRAMBreakdown:
    """
    Calculate VRAM requirements

    Args:
        model_size_b: Model size in billions of parameters
        quantization: Quantization type (e.g., 'Q4_K_M')
        context_size: Context window size in tokens
        batch_size: Batch size (usually 1 for llama.cpp server)

    Returns:
        VRAMBreakdown object
    """
    # Model VRAM
    if quantization not in QUANTIZATION_FACTORS:
        raise ValueError(
            f"Unknown quantization: {quantization}. Available: {list(QUANTIZATION_FACTORS.keys())}"
        )

    factor = QUANTIZATION_FACTORS[quantization]
    model_gb = model_size_b * factor

    # KV Cache VRAM (simplified formula)
    # More accurate would need model specs, but this is a good approximation
    kv_cache_gb = context_size * 0.00073  # Empirical for ~30B models

    # If we have model specs, use more accurate formula
    model_size_int = int(round(model_size_b))
    if model_size_int in MODEL_SPECS:
        specs = MODEL_SPECS[model_size_int]
        # VRAM_kv = 2 × layers × hidden_dim × context_size × precision / (8 × 1024³)
        # Assuming FP16 precision (2 bytes)
        kv_cache_gb = (2 * specs["layers"] * specs["hidden_dim"] * context_size * 2) / (
            8 * 1024**3
        )

    # Batch overhead (minimal for llama.cpp)
    batch_gb = batch_size * context_size * 0.0002 if batch_size > 1 else 0.0

    return VRAMBreakdown(
        model_gb=model_gb,
        kv_cache_gb=kv_cache_gb,
        overhead_gb=OVERHEAD_GB,
        batch_gb=batch_gb,
    )


def get_gpu_vram() -> float | None:
    """Try to detect GPU VRAM"""
    try:
        import subprocess

        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            vram_mb = int(result.stdout.strip().split("\n")[0])
            return vram_mb / 1024  # Convert to GB
    except:
        pass

    return None


def interactive_mode():
    """Interactive calculator"""
    print("\n╔═══════════════════════════════════════════════╗")
    print("║  VRAM Calculator - Interactive Mode           ║")
    print("╚═══════════════════════════════════════════════╝\n")

    # Model size
    print("📦 Model Size (in billions of parameters)")
    print("   Common: 7, 13, 30, 34, 70")
    model_size = float(input("   Enter model size: "))

    # Quantization
    print("\n🔢 Quantization Type")
    print(f"   Available: {', '.join(QUANTIZATION_FACTORS.keys())}")
    print("   Recommended: Q4_K_M (best quality/size balance)")
    quantization = input("   Enter quantization: ").upper()

    # Context size
    print("\n📝 Context Size (in tokens)")
    print("   Common: 2048, 4096, 8192, 16384")
    context_size = int(input("   Enter context size: "))

    # Batch size
    print("\n📊 Batch Size")
    print("   Default: 1 (llama.cpp server)")
    batch_input = input("   Enter batch size [1]: ").strip()
    batch_size = int(batch_input) if batch_input else 1

    # GPU VRAM
    auto_vram = get_gpu_vram()
    if auto_vram:
        print(f"\n🎮 Detected GPU VRAM: {auto_vram:.1f} GB")
        use_auto = input("   Use detected value? [Y/n]: ").strip().lower()
        gpu_vram = auto_vram if use_auto != "n" else None
    else:
        print("\n🎮 GPU VRAM (optional)")
        vram_input = input("   Enter GPU VRAM in GB (or press Enter to skip): ").strip()
        gpu_vram = float(vram_input) if vram_input else None

    # Calculate
    print("\n🔄 Calculating...\n")
    breakdown = calculate_vram(model_size, quantization, context_size, batch_size)
    print(breakdown.format_report(gpu_vram))
    print()


def main():
    parser = argparse.ArgumentParser(
        description="VRAM Calculator for LLM Inference",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Calculate for Qwen3-Coder-30B Q4_K_M with 4096 context on 24GB GPU
  %(prog)s --model-size 30 --quantization Q4_K_M --context-size 4096 --gpu-vram 24

  # Interactive mode
  %(prog)s --interactive

  # Quick check for 7B model
  %(prog)s -m 7 -q Q4_K_M -c 4096
        """,
    )

    parser.add_argument(
        "-i", "--interactive", action="store_true", help="Interactive mode"
    )
    parser.add_argument(
        "-m",
        "--model-size",
        type=float,
        help="Model size in billions of parameters (e.g., 7, 13, 30, 70)",
    )
    parser.add_argument(
        "-q",
        "--quantization",
        type=str,
        help=f"Quantization type: {', '.join(QUANTIZATION_FACTORS.keys())}",
    )
    parser.add_argument(
        "-c",
        "--context-size",
        type=int,
        help="Context window size in tokens (e.g., 2048, 4096, 8192)",
    )
    parser.add_argument(
        "-b", "--batch-size", type=int, default=1, help="Batch size (default: 1)"
    )
    parser.add_argument(
        "-g", "--gpu-vram", type=float, help="GPU VRAM in GB (optional, for comparison)"
    )
    parser.add_argument(
        "--auto-detect",
        action="store_true",
        help="Auto-detect GPU VRAM with nvidia-smi",
    )

    args = parser.parse_args()

    # Interactive mode
    if args.interactive:
        interactive_mode()
        return

    # Check required arguments
    if not all([args.model_size, args.quantization, args.context_size]):
        parser.error(
            "--model-size, --quantization, and --context-size are required (or use --interactive)"
        )

    # Auto-detect GPU if requested
    gpu_vram = args.gpu_vram
    if args.auto_detect and not gpu_vram:
        gpu_vram = get_gpu_vram()
        if gpu_vram:
            print(f"🎮 Detected GPU VRAM: {gpu_vram:.1f} GB\n")

    # Calculate
    try:
        breakdown = calculate_vram(
            args.model_size,
            args.quantization.upper(),
            args.context_size,
            args.batch_size,
        )

        print(breakdown.format_report(gpu_vram))
        print()

        # Exit code based on fit
        if gpu_vram and breakdown.total_gb > gpu_vram:
            sys.exit(1)  # Won't fit

    except ValueError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
