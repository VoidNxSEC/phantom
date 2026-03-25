# PHANTOM CLASSIFIER v0.0.1

**Data Classification, Sanitization, and Organization Pipeline**

```javascript
╔══════════════════════════════════════════════════════════════════════════════╗
║  ██████╗ ██╗  ██╗ █████╗ ███╗   ██╗████████╗ ██████╗ ███╗   ███╗              ║
║  ██╔══██╗██║  ██║██╔══██╗████╗  ██║╚══██╔══╝██╔═══██╗████╗ ████║              ║
║  ██████╔╝███████║███████║██╔██╗ ██║   ██║   ██║   ██║██╔████╔██║              ║
║  ██╔═══╝ ██╔══██║██╔══██║██║╚██╗██║   ██║   ██║   ██║██║╚██╔╝██║              ║
║  ██║     ██║  ██║██║  ██║██║ ╚████║   ██║   ╚██████╔╝██║ ╚═╝ ██║              ║
║  ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝    ╚═════╝ ╚═╝     ╚═╝              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

## Overview

Phantom Classifier is a directed acyclic graph (DAG) pipeline designed for:

- **Classification**: Multi-level detection utilizing magic bytes, file extensions, and content analysis.
- **Pseudonymization**: Cryptographically secure reversible mapping of file paths.
- **Integrity Verification**: Support for SHA256, BLAKE3, and xxHash algorithms.
- **Data Detection**: Pre-configured recognition of over 20 sensitive data patterns, including PII, credentials, and cryptographic keys.
- **Sanitization**: Capabilities for metadata stripping, pattern redaction, and full file sanitization.
- **Audit Logging**: Comprehensive chain of custody maintained via SQLite.
- **Concurrency**: Multi-threaded execution managing DAG task dependencies.

## Quick Start

```bash
# Enter the Nix environment
nix develop

# Process data
phantom -i /path/to/raw/data -o /path/to/organized -v

# Dry run (simulate execution without filesystem mutation)
phantom -i ./input -o ./output --dry-run

# View processing report
phantom-report ./organized
```

## Installation

### Nix Environment (Recommended)

```bash
# Clone the repository
cd phantom-classifier

# Enter the Nix development shell
nix develop

# Alternatively, execute directly via Nix run
nix run .#phantom -- -i ./input -o ./output
```

### Manual Dependencies (Linux/macOS)

```bash
# Required: Python 3.10+
pip install pandas numpy pyarrow python-magic chardet pynacl rich tqdm

# System dependencies
sudo apt install jq miller ripgrep fd-find exiftool b3sum
```

## Usage

### `phantom` - Primary Execution Interface

```bash
phantom -i <input_dir> -o <output_dir> [options]

Options:
  -i, --input     Input directory path (required)
  -o, --output    Output directory path (required)
  -w, --workers   Concurrency limit (default: logical CPU core count)
  -v, --verbose   Enable verbose logging output
  --dry-run       Simulate operations without modifying the filesystem
  --resolve       Resolve a given pseudonym back to its original path
```

### `phantom-dag` - DAG Orchestrator

```bash
phantom-dag -i <input_dir> -o <output_dir> [options]

Options:
  --sanitize      Sanitization policy level:
                  none   - No modifications (direct copy)
                  strip  - Remove file metadata (default)
                  pii    - Redact identified PII patterns
                  full   - Apply comprehensive sanitization
```

### Auxiliary Components

```bash
# Generate file hash manifest
phantom-hash ./directory > manifest.json

# Verify payload integrity against manifest hash
phantom-verify file.pdf abc123def456...

# Execute independent sensitive data scan
phantom-scan ./directory

# Aggregate and view execution reports
phantom-report ./output
```

## Architecture

### Pipeline Flow

```text
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  DISCOVERY  │────▶│ FINGERPRINT  │────▶│  CLASSIFY   │
└─────────────┘     └──────────────┘     └─────────────┘
                                                │
                    ┌──────────────────────────┘
                    ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   VERIFY    │◀────│  SANITIZE    │◀────│ PSEUDONYM   │
└─────────────┘     └──────────────┘     └─────────────┘
       │
       ▼
┌─────────────┐     ┌──────────────┐
│   PERSIST   │────▶│   REPORT     │
└─────────────┘     └──────────────┘
```

### Output File Structure

```text
output/
├── documents/          # PDF, DOCX, TXT, MD, etc.
├── images/             # PNG, JPG, GIF, SVG, etc.
├── audio/              # MP3, FLAC, WAV, etc.
├── video/              # MP4, MKV, AVI, etc.
├── code/               # PY, JS, RS, GO, NIX, etc.
├── data/               # JSON, CSV, PARQUET, DB, etc.
├── archives/           # ZIP, TAR, 7Z, etc.
├── configs/            # ENV, CONF, INI, etc.
├── logs/               # LOG, OUT, ERR, etc.
├── crypto/             # PEM, KEY, P12, etc.
├── executables/        # ELF, EXE, DEB, etc.
├── unknown/            # Unclassified binaries/files
└── .phantom/
    ├── phantom.db          # Operations database (SQLite)
    ├── pseudonym_map.json  # Reversible pseudonym mapping state
    ├── reports/            # Execution outputs in JSON
    ├── logs/               # Standard execution logs
    ├── audit/              # Operations audit trail
    ├── staging/            # Temporary processing storage
    └── quarantine/         # Files failing validation or processing
```

## Security & Reliability Mechanisms

### Cryptographic Algorithms

| Component | Usage Model                    | Performance Characteristic |
| --------- | ------------------------------ | -------------------------- |
| SHA256    | Primary integrity verification | Baseline                   |
| BLAKE3    | High-throughput verification   | High                       |
| xxHash    | Block-level/Streaming checks   | Maximum                    |

### Path Pseudonymization

```text
Input Path: /home/user/docs/secret_report_2024.pdf
Pseudonym:  PH-a1b2c3d4-e5f6a7b8-1234abcd.pdf
            │  │        │         │
            │  │        │         └─ Hexadecimal Timestamp
            │  │        └─ Random Entropy Block
            │  └─ Deterministic Path Hash
            └─ Identifier Prefix
```

### Data Pattern Recognition

The classifier natively identifies the following standard contexts:

- **PII Target Types**: Email addresses, Phone numbers, SSN, CPF/CNPJ (BR format), Payment Card Numbers.
- **Authentication Credentials**: Plaintext passwords, API keys, Bearer tokens.
- **Cloud Infrastructure Assets**: AWS Access Credentials, Standardized Connection Strings.
- **Cryptographic Material**: Private Keys, Public Certificates, PGP blocks.
- **Network Identifiers**: IPv4/IPv6 blocks, standard UUID patterns.

## Execution Reporting (JSON)

```json
{
  "phantom_version": "2.0.0",
  "statistics": {
    "total_files": 15420,
    "processed": 15398,
    "failed": 22,
    "success_rate": "99.86%",
    "total_size_human": "48.32 GB",
    "duration_seconds": "127.45",
    "throughput_files_per_sec": "120.81",
    "files_with_sensitive_data": 847
  },
  "classification_breakdown": {
    "documents": 3421,
    "images": 5842,
    "code": 2156,
    "data": 1893,
    "archives": 987,
    "configs": 534
  },
  "sensitivity_breakdown": {
    "PUBLIC": 12453,
    "INTERNAL": 1892,
    "CONFIDENTIAL": 734,
    "SECRET": 289,
    "TOP_SECRET": 30
  }
}
```

## Configuration and Extension

### Modifying Pattern Definitions

Append or override target contexts in `phantom_dag.py` via `SENSITIVE_PATTERNS`:

```python
SENSITIVE_PATTERNS = [
    # Format: (Regex Pattern, Identifier Label, Target Risk Score)
    (r'regex_pattern_definition', 'pattern_identifier', 0.8),
]
```

### Type Classification Extensions

Add custom MIME or extensions targeting specific `Classification` enums in `phantom_dag.py` (`EXT_MAP`):

```python
EXT_MAP = {
    '.custom_extension': Classification.TARGET_CATEGORY,
}
```

## Operational Workflows

### 1. Legacy Storage Normalization

```bash
phantom -i /mnt/legacy_storage -o /mnt/normalized_storage -w 8 -v
```

### 2. Sanitized Data Export

```bash
phantom-dag -i ./internal_dataset -o ./export_dataset --sanitize pii
```

### 3. Pre-Commit / Standalone Auditing

```bash
phantom-scan /home/user/project_repo | jq '.findings | .[] | select(.risk_score > 0.7)'
```

### 4. Verified State Transfer

```bash
# Generate source state
phantom-hash ./original > manifest_before.json

# Execute system copy/transfer
cp -r ./original ./transferred

# Generate target state
phantom-hash ./transferred > manifest_after.json

# Assert states
diff <(jq -S . manifest_before.json) <(jq -S . manifest_after.json)
```

## System Constraints

- Files exceeding 10MB are bypassed during the deep sensitive content scanning phase.
- File encryption prevents accurate content-based classification; parsing relies strictly on extension and magic bytes.
- Metadata stripping is executed on a best-effort basis for standard binaries and documents; proprietary formats may retain residual target metadata.

## License

This project is licensed under the Apache 2.0 License.

## Contributing

Pull requests are accepted. For architectural modifications or significant API changes, please open an issue describing the proposed design prior to execution.
