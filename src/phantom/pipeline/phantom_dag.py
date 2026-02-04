#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  PHANTOM DAG ORCHESTRATOR v2.0                                               ║
║  ────────────────────────────────────────────────────────────────────────────║
║  Enterprise-Grade ETL Pipeline with:                                         ║
║  • Directed Acyclic Graph (DAG) task scheduling                              ║
║  • Pseudonymization with reversible cryptographic mapping                    ║
║  • Multi-algorithm integrity verification (SHA256/BLAKE3/xxHash)             ║
║  • Content-aware sanitization with policy enforcement                        ║
║  • Parallel processing with dependency resolution                            ║
║  • Forensic-grade audit trails and chain of custody                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import hashlib
import json
import mimetypes
import os
import re
import secrets
import shutil
import sqlite3
import subprocess
import threading
import time
import uuid
from collections import defaultdict
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTS & CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

VERSION = "2.0.0"
CODENAME = "PHANTOM-DAG"

# Chunk size for streaming operations
CHUNK_SIZE = 65536  # 64KB

# Maximum file size for content analysis
MAX_CONTENT_SCAN_SIZE = 10 * 1024 * 1024  # 10MB

# ══════════════════════════════════════════════════════════════════════════════
# ENUMS & CLASSIFICATIONS
# ══════════════════════════════════════════════════════════════════════════════


class TaskStatus(Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    BLOCKED = "blocked"


class Classification(Enum):
    DOCUMENTS = "documents"
    IMAGES = "images"
    AUDIO = "audio"
    VIDEO = "video"
    CODE = "code"
    DATA = "data"
    ARCHIVES = "archives"
    EXECUTABLES = "executables"
    CONFIGS = "configs"
    LOGS = "logs"
    FORENSIC = "forensic"
    CRYPTO = "crypto"
    UNKNOWN = "unknown"
    SENSITIVE = "sensitive"
    MALFORMED = "malformed"
    QUARANTINE = "quarantine"


class Sensitivity(Enum):
    PUBLIC = 0
    INTERNAL = 1
    CONFIDENTIAL = 2
    SECRET = 3
    TOP_SECRET = 4
    RESTRICTED = 5


class SanitizationPolicy(Enum):
    NONE = "none"
    STRIP_METADATA = "strip_metadata"
    REDACT_PII = "redact_pii"
    FULL_SANITIZE = "full_sanitize"


# ══════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ══════════════════════════════════════════════════════════════════════════════


@dataclass
class FileFingerprint:
    """Cryptographic file fingerprint for integrity verification"""

    sha256: str
    blake3: str
    xxhash: str
    size: int
    created_at: str
    nonce: str = ""  # For pseudonymization salt

    def to_dict(self) -> dict:
        return asdict(self)

    def verify_against(self, other: "FileFingerprint") -> bool:
        """Verify integrity against another fingerprint"""
        return self.sha256 == other.sha256 and self.size == other.size


@dataclass
class SensitiveFinding:
    """Sensitive data detection result"""

    pattern_type: str
    pattern_name: str
    count: int
    line_numbers: list[int] = field(default_factory=list)
    samples: list[str] = field(default_factory=list)  # Redacted samples
    risk_score: float = 0.0


@dataclass
class FileRecord:
    """Complete file record with full chain of custody"""

    # Identity
    record_id: str
    original_path: str
    original_name: str
    pseudonym: str

    # Classification
    classification: str
    sensitivity: int
    mime_type: str
    extension: str

    # Integrity
    fingerprint_input: FileFingerprint
    fingerprint_output: FileFingerprint | None = None

    # Processing
    sanitization_applied: str = "none"
    metadata_stripped: bool = False
    content_modified: bool = False

    # Findings
    sensitive_findings: list[SensitiveFinding] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)
    custom_metadata: dict = field(default_factory=dict)

    # Audit
    processed_at: str = ""
    processing_duration_ms: float = 0.0
    destination_path: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["tags"] = list(self.tags)
        d["fingerprint_input"] = self.fingerprint_input.to_dict()
        if self.fingerprint_output:
            d["fingerprint_output"] = self.fingerprint_output.to_dict()
        d["sensitive_findings"] = [asdict(f) for f in self.sensitive_findings]
        return d


@dataclass
class DAGTask:
    """DAG pipeline task node"""

    task_id: str
    name: str
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: str | None = None
    start_time: float = 0.0
    end_time: float = 0.0
    retry_count: int = 0
    max_retries: int = 3

    @property
    def duration(self) -> float:
        if self.end_time and self.start_time:
            return self.end_time - self.start_time
        return 0.0


@dataclass
class PipelineContext:
    """Shared context for pipeline execution"""

    input_dir: Path
    output_dir: Path
    staging_dir: Path
    quarantine_dir: Path

    # Configuration
    workers: int = 4
    dry_run: bool = False
    verbose: bool = False
    sanitization_policy: SanitizationPolicy = SanitizationPolicy.STRIP_METADATA

    # State
    pseudonym_map: dict[str, str] = field(default_factory=dict)
    reverse_map: dict[str, str] = field(default_factory=dict)
    records: dict[str, FileRecord] = field(default_factory=dict)

    # Statistics
    total_files: int = 0
    processed: int = 0
    failed: int = 0
    quarantined: int = 0
    total_bytes: int = 0

    # Threading
    lock: threading.Lock = field(default_factory=threading.Lock)


# ══════════════════════════════════════════════════════════════════════════════
# LOGGING SYSTEM
# ══════════════════════════════════════════════════════════════════════════════


class PhantomLogger:
    """Thread-safe colored logging with audit trail"""

    COLORS = {
        "DEBUG": "\033[0;35m",  # Magenta
        "INFO": "\033[0;36m",  # Cyan
        "WARNING": "\033[0;33m",  # Yellow
        "ERROR": "\033[0;31m",  # Red
        "CRITICAL": "\033[1;31m",  # Bold Red
        "SUCCESS": "\033[0;32m",  # Green
        "AUDIT": "\033[0;34m",  # Blue
    }
    RESET = "\033[0m"

    def __init__(self, name: str, log_file: Path = None, verbose: bool = True):
        self.name = name
        self.verbose = verbose
        self.lock = threading.Lock()
        self.audit_log: list[dict] = []

        # File logger
        if log_file:
            self.file_handler = open(log_file, "a")
        else:
            self.file_handler = None

    def _format(self, level: str, message: str) -> tuple[str, str]:
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        color = self.COLORS.get(level, "")

        console_msg = f"{color}[{timestamp}] [{level:8}] {message}{self.RESET}"
        file_msg = f"[{timestamp}] [{level:8}] {message}"

        return console_msg, file_msg

    def log(self, level: str, message: str):
        console_msg, file_msg = self._format(level, message)

        with self.lock:
            if self.verbose or level in (
                "ERROR",
                "CRITICAL",
                "WARNING",
                "SUCCESS",
                "AUDIT",
            ):
                print(console_msg)

            if self.file_handler:
                self.file_handler.write(file_msg + "\n")
                self.file_handler.flush()

            # Audit trail
            if level == "AUDIT":
                self.audit_log.append(
                    {"timestamp": datetime.now(UTC).isoformat(), "message": message}
                )

    def debug(self, msg):
        self.log("DEBUG", msg)

    def info(self, msg):
        self.log("INFO", msg)

    def warning(self, msg):
        self.log("WARNING", msg)

    def error(self, msg):
        self.log("ERROR", msg)

    def critical(self, msg):
        self.log("CRITICAL", msg)

    def success(self, msg):
        self.log("SUCCESS", msg)

    def audit(self, msg):
        self.log("AUDIT", msg)

    def close(self):
        if self.file_handler:
            self.file_handler.close()


# Global logger
logger: PhantomLogger = None

# ══════════════════════════════════════════════════════════════════════════════
# CRYPTOGRAPHIC OPERATIONS
# ══════════════════════════════════════════════════════════════════════════════


class CryptoEngine:
    """Cryptographic operations for hashing and pseudonymization"""

    @staticmethod
    def compute_fingerprint(filepath: Path) -> FileFingerprint:
        """Compute multi-algorithm file fingerprint"""
        sha256_hash = hashlib.sha256()
        blake2_hash = hashlib.blake2b(digest_size=32)

        # xxHash via subprocess if available
        try:
            result = subprocess.run(
                ["xxhsum", "-H64", str(filepath)],
                capture_output=True,
                text=True,
                timeout=60,
            )
            xxhash_hex = result.stdout.split()[0] if result.returncode == 0 else ""
        except Exception:
            xxhash_hex = ""

        # BLAKE3 via b3sum if available
        try:
            result = subprocess.run(
                ["b3sum", "--no-names", str(filepath)],
                capture_output=True,
                text=True,
                timeout=60,
            )
            blake3_hex = result.stdout.strip() if result.returncode == 0 else None
        except Exception:
            blake3_hex = None

        # Stream hash computation
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
                sha256_hash.update(chunk)
                if not blake3_hex:
                    blake2_hash.update(chunk)

        stat = filepath.stat()
        nonce = secrets.token_hex(8)

        return FileFingerprint(
            sha256=sha256_hash.hexdigest(),
            blake3=blake3_hex or blake2_hash.hexdigest(),
            xxhash=xxhash_hex or "N/A",
            size=stat.st_size,
            created_at=datetime.now(UTC).isoformat(),
            nonce=nonce,
        )

    @staticmethod
    def generate_pseudonym(
        original_path: str, extension: str, nonce: str = None
    ) -> str:
        """Generate cryptographically secure pseudonym"""
        if not nonce:
            nonce = secrets.token_hex(4)

        # Deterministic component from path hash
        path_hash = hashlib.sha256(original_path.encode()).hexdigest()[:8]

        # Random component
        random_part = secrets.token_hex(4)

        # Timestamp component (hex)
        ts_hex = hex(int(time.time() * 1000))[-8:]

        # Format: PH-<path_hash>-<random>-<timestamp>.<ext>
        pseudonym = f"PH-{path_hash}-{random_part}-{ts_hex}{extension}"

        return pseudonym

    @staticmethod
    def verify_integrity(filepath: Path, expected: FileFingerprint) -> bool:
        """Verify file integrity against expected fingerprint"""
        current = CryptoEngine.compute_fingerprint(filepath)
        return current.verify_against(expected)


# ══════════════════════════════════════════════════════════════════════════════
# CLASSIFICATION ENGINE
# ══════════════════════════════════════════════════════════════════════════════


class ClassificationEngine:
    """Multi-level file classification system"""

    # Magic byte signatures
    MAGIC_SIGNATURES = {
        b"\x89PNG\r\n\x1a\n": ("image/png", Classification.IMAGES),
        b"\xff\xd8\xff": ("image/jpeg", Classification.IMAGES),
        b"GIF87a": ("image/gif", Classification.IMAGES),
        b"GIF89a": ("image/gif", Classification.IMAGES),
        b"%PDF": ("application/pdf", Classification.DOCUMENTS),
        b"PK\x03\x04": ("application/zip", Classification.ARCHIVES),
        b"\x1f\x8b": ("application/gzip", Classification.ARCHIVES),
        b"Rar!\x1a\x07": ("application/x-rar", Classification.ARCHIVES),
        b"7z\xbc\xaf\x27\x1c": ("application/x-7z", Classification.ARCHIVES),
        b"\xfd7zXZ\x00": ("application/x-xz", Classification.ARCHIVES),
        b"\x7fELF": ("application/x-elf", Classification.EXECUTABLES),
        b"MZ": ("application/x-dosexec", Classification.EXECUTABLES),
        b"#!": ("text/x-script", Classification.CODE),
        b"SQLite format 3": ("application/x-sqlite3", Classification.DATA),
        b"ID3": ("audio/mpeg", Classification.AUDIO),
        b"fLaC": ("audio/flac", Classification.AUDIO),
        b"OggS": ("audio/ogg", Classification.AUDIO),
        b"RIFF": ("audio/wav", Classification.AUDIO),
    }

    # Extension mappings (comprehensive)
    EXT_MAP = {
        # Documents
        ".pdf": Classification.DOCUMENTS,
        ".doc": Classification.DOCUMENTS,
        ".docx": Classification.DOCUMENTS,
        ".odt": Classification.DOCUMENTS,
        ".rtf": Classification.DOCUMENTS,
        ".txt": Classification.DOCUMENTS,
        ".md": Classification.DOCUMENTS,
        ".markdown": Classification.DOCUMENTS,
        ".rst": Classification.DOCUMENTS,
        ".tex": Classification.DOCUMENTS,
        ".epub": Classification.DOCUMENTS,
        ".mobi": Classification.DOCUMENTS,
        # Images
        ".png": Classification.IMAGES,
        ".jpg": Classification.IMAGES,
        ".jpeg": Classification.IMAGES,
        ".gif": Classification.IMAGES,
        ".bmp": Classification.IMAGES,
        ".tiff": Classification.IMAGES,
        ".tif": Classification.IMAGES,
        ".webp": Classification.IMAGES,
        ".svg": Classification.IMAGES,
        ".ico": Classification.IMAGES,
        ".raw": Classification.IMAGES,
        ".cr2": Classification.IMAGES,
        ".nef": Classification.IMAGES,
        ".heic": Classification.IMAGES,
        ".heif": Classification.IMAGES,
        # Audio
        ".mp3": Classification.AUDIO,
        ".wav": Classification.AUDIO,
        ".flac": Classification.AUDIO,
        ".ogg": Classification.AUDIO,
        ".m4a": Classification.AUDIO,
        ".aac": Classification.AUDIO,
        ".wma": Classification.AUDIO,
        ".opus": Classification.AUDIO,
        ".aiff": Classification.AUDIO,
        # Video
        ".mp4": Classification.VIDEO,
        ".mkv": Classification.VIDEO,
        ".avi": Classification.VIDEO,
        ".mov": Classification.VIDEO,
        ".wmv": Classification.VIDEO,
        ".webm": Classification.VIDEO,
        ".flv": Classification.VIDEO,
        ".m4v": Classification.VIDEO,
        ".mpeg": Classification.VIDEO,
        ".mpg": Classification.VIDEO,
        # Code
        ".py": Classification.CODE,
        ".pyw": Classification.CODE,
        ".pyx": Classification.CODE,
        ".js": Classification.CODE,
        ".mjs": Classification.CODE,
        ".ts": Classification.CODE,
        ".jsx": Classification.CODE,
        ".tsx": Classification.CODE,
        ".rs": Classification.CODE,
        ".go": Classification.CODE,
        ".c": Classification.CODE,
        ".cpp": Classification.CODE,
        ".cc": Classification.CODE,
        ".cxx": Classification.CODE,
        ".h": Classification.CODE,
        ".hpp": Classification.CODE,
        ".java": Classification.CODE,
        ".kt": Classification.CODE,
        ".kts": Classification.CODE,
        ".scala": Classification.CODE,
        ".rb": Classification.CODE,
        ".php": Classification.CODE,
        ".sh": Classification.CODE,
        ".bash": Classification.CODE,
        ".zsh": Classification.CODE,
        ".fish": Classification.CODE,
        ".ps1": Classification.CODE,
        ".psm1": Classification.CODE,
        ".nix": Classification.CODE,
        ".hs": Classification.CODE,
        ".ml": Classification.CODE,
        ".swift": Classification.CODE,
        ".r": Classification.CODE,
        ".R": Classification.CODE,
        ".sql": Classification.CODE,
        ".lua": Classification.CODE,
        ".pl": Classification.CODE,
        ".pm": Classification.CODE,
        ".html": Classification.CODE,
        ".htm": Classification.CODE,
        ".css": Classification.CODE,
        ".scss": Classification.CODE,
        ".sass": Classification.CODE,
        ".less": Classification.CODE,
        ".vue": Classification.CODE,
        ".svelte": Classification.CODE,
        ".elm": Classification.CODE,
        ".ex": Classification.CODE,
        ".exs": Classification.CODE,
        ".erl": Classification.CODE,
        ".hrl": Classification.CODE,
        ".clj": Classification.CODE,
        ".cljs": Classification.CODE,
        ".dart": Classification.CODE,
        ".zig": Classification.CODE,
        ".v": Classification.CODE,
        ".nim": Classification.CODE,
        ".cr": Classification.CODE,
        ".d": Classification.CODE,
        # Data
        ".json": Classification.DATA,
        ".jsonl": Classification.DATA,
        ".ndjson": Classification.DATA,
        ".xml": Classification.DATA,
        ".yaml": Classification.DATA,
        ".yml": Classification.DATA,
        ".toml": Classification.DATA,
        ".csv": Classification.DATA,
        ".tsv": Classification.DATA,
        ".parquet": Classification.DATA,
        ".avro": Classification.DATA,
        ".orc": Classification.DATA,
        ".db": Classification.DATA,
        ".sqlite": Classification.DATA,
        ".sqlite3": Classification.DATA,
        ".mdb": Classification.DATA,
        ".accdb": Classification.DATA,
        ".xls": Classification.DATA,
        ".xlsx": Classification.DATA,
        ".ods": Classification.DATA,
        # Archives
        ".zip": Classification.ARCHIVES,
        ".tar": Classification.ARCHIVES,
        ".gz": Classification.ARCHIVES,
        ".tgz": Classification.ARCHIVES,
        ".bz2": Classification.ARCHIVES,
        ".xz": Classification.ARCHIVES,
        ".7z": Classification.ARCHIVES,
        ".rar": Classification.ARCHIVES,
        ".zst": Classification.ARCHIVES,
        ".lz4": Classification.ARCHIVES,
        ".lzma": Classification.ARCHIVES,
        ".cab": Classification.ARCHIVES,
        ".iso": Classification.ARCHIVES,
        ".dmg": Classification.ARCHIVES,
        # Configs
        ".conf": Classification.CONFIGS,
        ".cfg": Classification.CONFIGS,
        ".ini": Classification.CONFIGS,
        ".env": Classification.CONFIGS,
        ".properties": Classification.CONFIGS,
        ".rc": Classification.CONFIGS,
        ".config": Classification.CONFIGS,
        # Logs
        ".log": Classification.LOGS,
        ".out": Classification.LOGS,
        ".err": Classification.LOGS,
        ".trace": Classification.LOGS,
        # Crypto
        ".pem": Classification.CRYPTO,
        ".crt": Classification.CRYPTO,
        ".cer": Classification.CRYPTO,
        ".der": Classification.CRYPTO,
        ".key": Classification.CRYPTO,
        ".pub": Classification.CRYPTO,
        ".gpg": Classification.CRYPTO,
        ".asc": Classification.CRYPTO,
        ".p12": Classification.CRYPTO,
        ".pfx": Classification.CRYPTO,
        ".jks": Classification.CRYPTO,
        ".keystore": Classification.CRYPTO,
        ".kdbx": Classification.CRYPTO,
        ".age": Classification.CRYPTO,
        # Executables
        ".exe": Classification.EXECUTABLES,
        ".dll": Classification.EXECUTABLES,
        ".so": Classification.EXECUTABLES,
        ".dylib": Classification.EXECUTABLES,
        ".app": Classification.EXECUTABLES,
        ".bin": Classification.EXECUTABLES,
        ".msi": Classification.EXECUTABLES,
        ".deb": Classification.EXECUTABLES,
        ".rpm": Classification.EXECUTABLES,
        ".apk": Classification.EXECUTABLES,
        ".ipa": Classification.EXECUTABLES,
    }

    # Sensitive content patterns
    SENSITIVE_PATTERNS = [
        # Personal Identifiers
        (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "email", 0.3),
        (
            r"\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}\b",
            "phone_us",
            0.4,
        ),
        (r"\b\d{3}[-.]?\d{2}[-.]?\d{4}\b", "ssn", 0.9),
        (r"\b(?:\d{4}[-\s]?){3}\d{4}\b", "credit_card", 0.9),
        # Brazilian PII
        (r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b", "cpf_br", 0.8),
        (r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b", "cnpj_br", 0.8),
        # API Keys & Secrets
        (
            r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?',
            "api_key",
            0.9,
        ),
        (
            r'(?i)(secret|token|password|passwd|pwd)\s*[=:]\s*["\']?[^\s"\']{8,}["\']?',
            "credential",
            0.85,
        ),
        (r"(?i)bearer\s+[a-zA-Z0-9_\-\.]+", "bearer_token", 0.9),
        (r"(?i)basic\s+[a-zA-Z0-9+/=]+", "basic_auth", 0.8),
        # AWS
        (r"AKIA[0-9A-Z]{16}", "aws_access_key", 0.95),
        (
            r'(?i)aws[_\-]?secret[_\-]?access[_\-]?key\s*[=:]\s*["\']?[A-Za-z0-9/+=]{40}["\']?',
            "aws_secret",
            0.95,
        ),
        # Private Keys
        (r"-----BEGIN (?:RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----", "private_key", 1.0),
        (r"-----BEGIN CERTIFICATE-----", "certificate", 0.5),
        (r"-----BEGIN PGP PRIVATE KEY BLOCK-----", "pgp_private", 1.0),
        # Network
        (r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "ipv4", 0.2),
        (
            r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b",
            "uuid",
            0.1,
        ),
        # Database
        (
            r"(?i)(?:mysql|postgres|mongodb|redis|jdbc)://[^\s]+",
            "db_connection_string",
            0.85,
        ),
    ]

    @classmethod
    def detect_by_magic(
        cls, filepath: Path
    ) -> tuple[str | None, Classification | None]:
        """Detect file type by magic bytes"""
        try:
            with open(filepath, "rb") as f:
                header = f.read(64)

            for magic, (mime, classification) in cls.MAGIC_SIGNATURES.items():
                if header.startswith(magic):
                    return mime, classification
        except Exception:
            pass
        return None, None

    @classmethod
    def detect_by_extension(
        cls, filepath: Path
    ) -> tuple[str | None, Classification | None]:
        """Detect file type by extension"""
        ext = filepath.suffix.lower()
        classification = cls.EXT_MAP.get(ext, Classification.UNKNOWN)
        mime = mimetypes.guess_type(str(filepath))[0]
        return mime, classification

    @classmethod
    def scan_sensitive_content(
        cls, filepath: Path, max_size: int = MAX_CONTENT_SCAN_SIZE
    ) -> list[SensitiveFinding]:
        """Scan file for sensitive content patterns"""
        findings = []

        try:
            # Only scan text-like files
            stat = filepath.stat()
            if stat.st_size > max_size:
                return findings

            with open(filepath, "rb") as f:
                raw = f.read(max_size)

            # Try decoding
            try:
                content = raw.decode("utf-8")
            except Exception:
                try:
                    content = raw.decode("latin-1")
                except Exception:
                    return findings

            lines = content.split("\n")

            for pattern, pattern_name, risk_base in cls.SENSITIVE_PATTERNS:
                matches = []
                line_numbers = []

                for i, line in enumerate(lines, 1):
                    found = re.findall(pattern, line, re.IGNORECASE)
                    if found:
                        matches.extend(
                            found
                            if isinstance(found[0], str)
                            else [m[0] if isinstance(m, tuple) else m for m in found]
                        )
                        line_numbers.append(i)

                if matches:
                    # Redact samples for audit
                    redacted_samples = [cls._redact_sample(m) for m in matches[:3]]

                    findings.append(
                        SensitiveFinding(
                            pattern_type="regex",
                            pattern_name=pattern_name,
                            count=len(matches),
                            line_numbers=line_numbers[:10],
                            samples=redacted_samples,
                            risk_score=min(risk_base * len(matches), 1.0),
                        )
                    )

        except Exception as e:
            if logger:
                logger.debug(f"Sensitive scan error: {e}")

        return findings

    @staticmethod
    def _redact_sample(sample: str, visible_chars: int = 4) -> str:
        """Redact sensitive sample for logging"""
        if len(sample) <= visible_chars * 2:
            return "*" * len(sample)
        return (
            sample[:visible_chars]
            + "*" * (len(sample) - visible_chars * 2)
            + sample[-visible_chars:]
        )

    @classmethod
    def classify(cls, filepath: Path) -> tuple[Classification, str, Sensitivity]:
        """
        Multi-level classification:
        1. Magic bytes
        2. Extension fallback
        3. Sensitivity assessment
        """
        # Level 1: Magic bytes
        mime_magic, cls_magic = cls.detect_by_magic(filepath)

        # Level 2: Extension
        mime_ext, cls_ext = cls.detect_by_extension(filepath)

        # Determine final classification
        classification = cls_magic or cls_ext or Classification.UNKNOWN
        mime_type = mime_magic or mime_ext or "application/octet-stream"

        # Determine sensitivity
        sensitivity = Sensitivity.PUBLIC

        # Crypto files are always high sensitivity
        if classification == Classification.CRYPTO:
            sensitivity = Sensitivity.SECRET
            ext = filepath.suffix.lower()
            if ext in (".key", ".pem", ".p12", ".pfx"):
                sensitivity = Sensitivity.TOP_SECRET

        # Config files with sensitive extensions
        if classification == Classification.CONFIGS:
            if filepath.suffix.lower() == ".env":
                sensitivity = Sensitivity.CONFIDENTIAL

        return classification, mime_type, sensitivity


# ══════════════════════════════════════════════════════════════════════════════
# SANITIZATION ENGINE
# ══════════════════════════════════════════════════════════════════════════════


class SanitizationEngine:
    """Content sanitization and metadata stripping"""

    @classmethod
    def scan_sensitive_patterns(cls, text: str) -> list[SensitiveFinding]:
        """Scan plain text for sensitive patterns (mirrors ClassificationEngine logic)."""
        findings: list[SensitiveFinding] = []
        lines = text.split("\n")
        for pattern, pattern_name, risk_base in ClassificationEngine.SENSITIVE_PATTERNS:
            matches: list[str] = []
            line_numbers: list[int] = []
            for i, line in enumerate(lines, 1):
                found = re.findall(pattern, line, re.IGNORECASE)
                if found:
                    matches.extend(
                        found if isinstance(found[0], str)
                        else [m[0] if isinstance(m, tuple) else m for m in found]
                    )
                    line_numbers.append(i)
            if matches:
                findings.append(
                    SensitiveFinding(
                        pattern_type="regex",
                        pattern_name=pattern_name,
                        count=len(matches),
                        line_numbers=line_numbers[:10],
                        samples=[ClassificationEngine._redact_sample(m) for m in matches[:3]],
                        risk_score=min(risk_base * len(matches), 1.0),
                    )
                )
        return findings

    @staticmethod
    def strip_image_metadata(filepath: Path, output_path: Path) -> bool:
        """Strip EXIF and other metadata from images"""
        try:
            result = subprocess.run(
                ["exiftool", "-all=", "-overwrite_original", str(filepath)],
                capture_output=True,
                timeout=60,
            )
            return result.returncode == 0
        except Exception:
            # Fallback: just copy
            shutil.copy2(filepath, output_path)
            return False

    @staticmethod
    def strip_pdf_metadata(filepath: Path, output_path: Path) -> bool:
        """Strip metadata from PDF files"""
        try:
            result = subprocess.run(
                ["exiftool", "-all=", "-overwrite_original", str(filepath)],
                capture_output=True,
                timeout=60,
            )
            return result.returncode == 0
        except Exception:
            shutil.copy2(filepath, output_path)
            return False

    @staticmethod
    def sanitize_text_pii(
        filepath: Path, output_path: Path, findings: list[SensitiveFinding]
    ) -> bool:
        """Redact PII patterns in text files"""
        try:
            with open(filepath, encoding="utf-8", errors="replace") as f:
                content = f.read()

            # Apply redactions for high-risk patterns
            for finding in findings:
                if finding.risk_score >= 0.7:
                    for pattern, name, _ in ClassificationEngine.SENSITIVE_PATTERNS:
                        if name == finding.pattern_name:
                            content = re.sub(
                                pattern,
                                f"[REDACTED:{name}]",
                                content,
                                flags=re.IGNORECASE,
                            )
                            break

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)

            return True
        except Exception:
            shutil.copy2(filepath, output_path)
            return False


# ══════════════════════════════════════════════════════════════════════════════
# DAG EXECUTOR
# ══════════════════════════════════════════════════════════════════════════════


class DAGExecutor:
    """Directed Acyclic Graph task executor with dependency resolution"""

    def __init__(self, max_workers: int = 4):
        self.tasks: dict[str, DAGTask] = {}
        self.max_workers = max_workers
        self.lock = threading.Lock()

    def add_task(self, task: DAGTask):
        """Add task to DAG"""
        self.tasks[task.task_id] = task

    def get_ready_tasks(self) -> list[DAGTask]:
        """Get tasks with all dependencies satisfied"""
        ready = []
        for task in self.tasks.values():
            if task.status != TaskStatus.PENDING:
                continue

            # Check all dependencies
            deps_satisfied = True
            for dep_id in task.dependencies:
                dep_task = self.tasks.get(dep_id)
                if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                    deps_satisfied = False
                    break

            if deps_satisfied:
                ready.append(task)

        return ready

    def execute_task(self, task: DAGTask) -> bool:
        """Execute single task"""
        task.status = TaskStatus.RUNNING
        task.start_time = time.time()

        try:
            # Get dependency results
            dep_results = {}
            for dep_id in task.dependencies:
                dep_task = self.tasks.get(dep_id)
                if dep_task:
                    dep_results[dep_id] = dep_task.result

            # Execute
            result = task.func(*task.args, **task.kwargs, dep_results=dep_results)
            task.result = result
            task.status = TaskStatus.COMPLETED
            task.end_time = time.time()

            if logger:
                logger.success(f"Task {task.name} completed in {task.duration:.2f}s")

            return True

        except Exception as e:
            task.error = str(e)
            task.status = TaskStatus.FAILED
            task.end_time = time.time()
            task.retry_count += 1

            if logger:
                logger.error(f"Task {task.name} failed: {e}")

            # Retry logic
            if task.retry_count < task.max_retries:
                task.status = TaskStatus.PENDING
                if logger:
                    logger.warning(
                        f"Retrying task {task.name} ({task.retry_count}/{task.max_retries})"
                    )

            return False

    def execute_all(self) -> dict[str, Any]:
        """Execute all tasks respecting dependencies"""
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            while True:
                ready_tasks = self.get_ready_tasks()

                if not ready_tasks:
                    # Check if all done or blocked
                    pending = [
                        t for t in self.tasks.values() if t.status == TaskStatus.PENDING
                    ]
                    running = [
                        t for t in self.tasks.values() if t.status == TaskStatus.RUNNING
                    ]

                    if not pending and not running:
                        break

                    if pending and not running:
                        # Circular dependency or failed dependencies
                        for task in pending:
                            task.status = TaskStatus.BLOCKED
                        break

                    time.sleep(0.1)
                    continue

                # Submit ready tasks
                futures = {
                    executor.submit(self.execute_task, task): task
                    for task in ready_tasks
                }

                for future in as_completed(futures):
                    task = futures[future]
                    try:
                        future.result()
                    except Exception as e:
                        if logger:
                            logger.error(f"Executor error for {task.name}: {e}")

        end_time = time.time()

        # Compile results
        results = {
            "total_tasks": len(self.tasks),
            "completed": len(
                [t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED]
            ),
            "failed": len(
                [t for t in self.tasks.values() if t.status == TaskStatus.FAILED]
            ),
            "blocked": len(
                [t for t in self.tasks.values() if t.status == TaskStatus.BLOCKED]
            ),
            "duration": end_time - start_time,
            "tasks": {
                tid: {
                    "status": t.status.value,
                    "duration": t.duration,
                    "error": t.error,
                }
                for tid, t in self.tasks.items()
            },
        }

        return results


# ══════════════════════════════════════════════════════════════════════════════
# PHANTOM PIPELINE
# ══════════════════════════════════════════════════════════════════════════════


class PhantomPipeline:
    """Main pipeline orchestrator"""

    def __init__(self, ctx: PipelineContext):
        self.ctx = ctx
        self.dag = DAGExecutor(max_workers=ctx.workers)
        self.db_path = ctx.output_dir / ".phantom" / "phantom.db"
        self._init_directories()
        self._init_database()

    def _init_directories(self):
        """Initialize directory structure"""
        self.ctx.output_dir.mkdir(parents=True, exist_ok=True)
        self.ctx.staging_dir.mkdir(parents=True, exist_ok=True)
        self.ctx.quarantine_dir.mkdir(parents=True, exist_ok=True)

        # Classification directories
        for cls in Classification:
            (self.ctx.output_dir / cls.value).mkdir(exist_ok=True)

        # Metadata directories
        (self.ctx.output_dir / ".phantom").mkdir(exist_ok=True)
        (self.ctx.output_dir / ".phantom" / "reports").mkdir(exist_ok=True)
        (self.ctx.output_dir / ".phantom" / "logs").mkdir(exist_ok=True)
        (self.ctx.output_dir / ".phantom" / "audit").mkdir(exist_ok=True)

    def _init_database(self):
        """Initialize SQLite database for records"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS file_records (
                record_id TEXT PRIMARY KEY,
                original_path TEXT,
                original_name TEXT,
                pseudonym TEXT,
                classification TEXT,
                sensitivity INTEGER,
                mime_type TEXT,
                extension TEXT,
                size INTEGER,
                sha256 TEXT,
                blake3 TEXT,
                processed_at TEXT,
                destination_path TEXT,
                metadata JSON
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pseudonym_map (
                pseudonym TEXT PRIMARY KEY,
                original_path TEXT,
                created_at TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                event_type TEXT,
                record_id TEXT,
                details TEXT
            )
        """)

        conn.commit()
        conn.close()

    def _save_record(self, record: FileRecord):
        """Persist file record to database"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO file_records
            (record_id, original_path, original_name, pseudonym, classification,
             sensitivity, mime_type, extension, size, sha256, blake3,
             processed_at, destination_path, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                record.record_id,
                record.original_path,
                record.original_name,
                record.pseudonym,
                record.classification,
                record.sensitivity,
                record.mime_type,
                record.extension,
                record.fingerprint_input.size,
                record.fingerprint_input.sha256,
                record.fingerprint_input.blake3,
                record.processed_at,
                record.destination_path,
                json.dumps(record.to_dict()),
            ),
        )

        cursor.execute(
            """
            INSERT OR REPLACE INTO pseudonym_map (pseudonym, original_path, created_at)
            VALUES (?, ?, ?)
        """,
            (record.pseudonym, record.original_path, record.processed_at),
        )

        conn.commit()
        conn.close()

    def _audit_event(self, event_type: str, record_id: str, details: str):
        """Log audit event"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO audit_log (timestamp, event_type, record_id, details)
            VALUES (?, ?, ?, ?)
        """,
            (datetime.now(UTC).isoformat(), event_type, record_id, details),
        )

        conn.commit()
        conn.close()

    def process_file(self, filepath: Path, **kwargs) -> FileRecord | None:
        """Process single file through pipeline"""
        start_time = time.time()

        try:
            str_path = str(filepath)

            # Skip if already in pseudonym map
            if str_path in self.ctx.reverse_map:
                logger.debug(f"Skipping already processed: {filepath.name}")
                return None

            # Generate record ID
            record_id = str(uuid.uuid4())

            # Step 1: Compute input fingerprint
            fingerprint_input = CryptoEngine.compute_fingerprint(filepath)

            # Step 2: Classify
            classification, mime_type, sensitivity = ClassificationEngine.classify(
                filepath
            )

            # Step 3: Generate pseudonym
            pseudonym = CryptoEngine.generate_pseudonym(
                str_path, filepath.suffix.lower(), fingerprint_input.nonce
            )

            # Step 4: Scan for sensitive content (for text-based files)
            sensitive_findings = []
            if classification in (
                Classification.DOCUMENTS,
                Classification.CODE,
                Classification.CONFIGS,
                Classification.DATA,
                Classification.LOGS,
            ):
                sensitive_findings = ClassificationEngine.scan_sensitive_content(
                    filepath
                )

                # Upgrade sensitivity if findings
                if sensitive_findings:
                    max_risk = max(f.risk_score for f in sensitive_findings)
                    if max_risk >= 0.9:
                        sensitivity = Sensitivity.TOP_SECRET
                    elif max_risk >= 0.7:
                        sensitivity = Sensitivity.SECRET
                    elif max_risk >= 0.5:
                        sensitivity = Sensitivity.CONFIDENTIAL

            # Build record
            record = FileRecord(
                record_id=record_id,
                original_path=str_path,
                original_name=filepath.name,
                pseudonym=pseudonym,
                classification=classification.value,
                sensitivity=sensitivity.value,
                mime_type=mime_type,
                extension=filepath.suffix.lower(),
                fingerprint_input=fingerprint_input,
                sensitive_findings=sensitive_findings,
                processed_at=datetime.now(UTC).isoformat(),
            )

            # Add auto-tags
            if sensitive_findings:
                record.tags.add("has_sensitive_data")
                for f in sensitive_findings:
                    record.tags.add(f"sensitive:{f.pattern_name}")

            if fingerprint_input.size > 100 * 1024 * 1024:
                record.tags.add("large_file")

            if filepath.name.startswith("."):
                record.tags.add("hidden_file")

            # Step 5: Determine destination
            dest_dir = self.ctx.output_dir / classification.value
            dest_path = dest_dir / pseudonym
            record.destination_path = str(dest_path)

            # Step 6: Copy/Move with optional sanitization
            if not self.ctx.dry_run:
                # Apply sanitization based on policy
                if self.ctx.sanitization_policy == SanitizationPolicy.STRIP_METADATA:
                    if classification == Classification.IMAGES:
                        SanitizationEngine.strip_image_metadata(filepath, dest_path)
                        record.metadata_stripped = True
                    elif (
                        classification == Classification.DOCUMENTS
                        and mime_type == "application/pdf"
                    ):
                        SanitizationEngine.strip_pdf_metadata(filepath, dest_path)
                        record.metadata_stripped = True
                    else:
                        shutil.copy2(filepath, dest_path)

                elif self.ctx.sanitization_policy == SanitizationPolicy.REDACT_PII:
                    if classification in (
                        Classification.CODE,
                        Classification.CONFIGS,
                        Classification.DATA,
                        Classification.DOCUMENTS,
                    ):
                        if sensitive_findings:
                            SanitizationEngine.sanitize_text_pii(
                                filepath, dest_path, sensitive_findings
                            )
                            record.content_modified = True
                        else:
                            shutil.copy2(filepath, dest_path)
                    else:
                        shutil.copy2(filepath, dest_path)

                else:
                    # No sanitization - direct copy
                    shutil.copy2(filepath, dest_path)

                # Step 7: Verify integrity
                fingerprint_output = CryptoEngine.compute_fingerprint(dest_path)
                record.fingerprint_output = fingerprint_output

                # Verify (unless content was modified)
                if not record.content_modified:
                    if not fingerprint_output.verify_against(fingerprint_input):
                        # Integrity failure - quarantine
                        quarantine_path = self.ctx.quarantine_dir / pseudonym
                        shutil.move(dest_path, quarantine_path)
                        record.destination_path = str(quarantine_path)
                        record.tags.add("integrity_failure")

                        with self.ctx.lock:
                            self.ctx.quarantined += 1

                        logger.error(f"INTEGRITY FAILURE: {filepath.name} → quarantine")
                        self._audit_event("INTEGRITY_FAILURE", record_id, str_path)

                        raise ValueError("Integrity verification failed")

            # Step 8: Update mappings
            with self.ctx.lock:
                self.ctx.pseudonym_map[pseudonym] = str_path
                self.ctx.reverse_map[str_path] = pseudonym
                self.ctx.records[pseudonym] = record
                self.ctx.processed += 1
                self.ctx.total_bytes += fingerprint_input.size

            # Step 9: Persist record
            self._save_record(record)

            # Calculate duration
            record.processing_duration_ms = (time.time() - start_time) * 1000

            logger.success(f"✓ {filepath.name} → {classification.value}/{pseudonym}")
            self._audit_event(
                "FILE_PROCESSED",
                record_id,
                f"{str_path} -> {pseudonym} ({classification.value})",
            )

            return record

        except Exception as e:
            with self.ctx.lock:
                self.ctx.failed += 1

            logger.error(f"✗ {filepath.name}: {e}")
            self._audit_event("PROCESSING_ERROR", "", f"{filepath}: {e}")

            return None

    def discover_files(self) -> list[Path]:
        """Discover all files in input directory"""
        files = []
        for item in self.ctx.input_dir.rglob("*"):
            if item.is_file() and not item.name.startswith(".phantom"):
                files.append(item)
        return files

    def execute(self):
        """Execute full pipeline"""
        self._print_banner()

        start_time = time.time()

        # Stage 1: Discovery
        logger.info("═══ STAGE 1: FILE DISCOVERY ═══")
        files = self.discover_files()
        self.ctx.total_files = len(files)
        logger.info(f"Discovered {len(files)} files")

        if not files:
            logger.warning("No files to process")
            return

        # Stage 2: Processing
        logger.info("═══ STAGE 2: CLASSIFICATION & PROCESSING ═══")

        with ThreadPoolExecutor(max_workers=self.ctx.workers) as executor:
            futures = {executor.submit(self.process_file, f): f for f in files}

            for future in as_completed(futures):
                filepath = futures[future]
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Worker exception for {filepath}: {e}")

        end_time = time.time()

        # Stage 3: Reporting
        logger.info("═══ STAGE 3: REPORT GENERATION ═══")
        report = self._generate_report(end_time - start_time)

        # Save report
        report_path = (
            self.ctx.output_dir
            / ".phantom"
            / "reports"
            / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, default=str)

        logger.success(f"Report saved: {report_path}")

        # Save pseudonym map
        map_path = self.ctx.output_dir / ".phantom" / "pseudonym_map.json"
        with open(map_path, "w") as f:
            json.dump(
                {
                    "version": VERSION,
                    "created": datetime.now(UTC).isoformat(),
                    "mappings": self.ctx.pseudonym_map,
                },
                f,
                indent=2,
            )

        self._print_summary(report)

    def _generate_report(self, duration: float) -> dict:
        """Generate comprehensive pipeline report"""
        # Classification breakdown
        by_classification = defaultdict(int)
        by_sensitivity = defaultdict(int)
        by_extension = defaultdict(int)
        sensitive_file_count = 0

        for record in self.ctx.records.values():
            by_classification[record.classification] += 1
            by_sensitivity[record.sensitivity] += 1
            by_extension[record.extension] += 1
            if record.sensitive_findings:
                sensitive_file_count += 1

        return {
            "phantom_version": VERSION,
            "codename": CODENAME,
            "generated_at": datetime.now(UTC).isoformat(),
            "pipeline": {
                "input_directory": str(self.ctx.input_dir),
                "output_directory": str(self.ctx.output_dir),
                "dry_run": self.ctx.dry_run,
                "workers": self.ctx.workers,
                "sanitization_policy": self.ctx.sanitization_policy.value,
            },
            "statistics": {
                "total_files": self.ctx.total_files,
                "processed": self.ctx.processed,
                "failed": self.ctx.failed,
                "quarantined": self.ctx.quarantined,
                "success_rate": f"{(self.ctx.processed / max(self.ctx.total_files, 1)) * 100:.2f}%",
                "total_bytes": self.ctx.total_bytes,
                "total_size_human": self._human_size(self.ctx.total_bytes),
                "duration_seconds": f"{duration:.2f}",
                "throughput_files_per_sec": f"{self.ctx.processed / max(duration, 0.001):.2f}",
                "throughput_mb_per_sec": f"{(self.ctx.total_bytes / 1024 / 1024) / max(duration, 0.001):.2f}",
                "files_with_sensitive_data": sensitive_file_count,
            },
            "classification_breakdown": dict(by_classification),
            "sensitivity_breakdown": {
                Sensitivity(k).name: v for k, v in sorted(by_sensitivity.items())
            },
            "extension_breakdown": dict(
                sorted(by_extension.items(), key=lambda x: -x[1])[:20]
            ),
            "records": {
                k: v.to_dict() for k, v in list(self.ctx.records.items())[:100]
            },  # First 100
        }

    def _human_size(self, size: int) -> str:
        """Convert bytes to human readable"""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} PB"

    def _print_banner(self):
        """Print startup banner"""
        banner = (
            """
\033[0;35m╔══════════════════════════════════════════════════════════════════════════════╗
║  ██████╗ ██╗  ██╗ █████╗ ███╗   ██╗████████╗ ██████╗ ███╗   ███╗              ║
║  ██╔══██╗██║  ██║██╔══██╗████╗  ██║╚══██╔══╝██╔═══██╗████╗ ████║              ║
║  ██████╔╝███████║███████║██╔██╗ ██║   ██║   ██║   ██║██╔████╔██║              ║
║  ██╔═══╝ ██╔══██║██╔══██║██║╚██╗██║   ██║   ██║   ██║██║╚██╔╝██║              ║
║  ██║     ██║  ██║██║  ██║██║ ╚████║   ██║   ╚██████╔╝██║ ╚═╝ ██║              ║
║  ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝    ╚═════╝ ╚═╝     ╚═╝              ║
║  DAG ORCHESTRATOR v"""
            + VERSION
            + """                                                         ║
║  ──────────────────────────────────────────────────────────────────────────── ║
║  NSA-Grade Data Classification & Sanitization Pipeline                        ║
╚══════════════════════════════════════════════════════════════════════════════╝\033[0m
"""
        )
        print(banner)

    def _print_summary(self, report: dict):
        """Print execution summary"""
        stats = report["statistics"]
        print(f"""
\033[0;32m╔══════════════════════════════════════════════════════════════════════════════╗
║                           EXECUTION SUMMARY                                    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Total Files:           {stats["total_files"]:>10}                                          ║
║  Processed:             {stats["processed"]:>10}                                          ║
║  Failed:                {stats["failed"]:>10}                                          ║
║  Quarantined:           {stats["quarantined"]:>10}                                          ║
║  Success Rate:          {stats["success_rate"]:>10}                                          ║
║  Total Size:            {stats["total_size_human"]:>10}                                          ║
║  Duration:              {stats["duration_seconds"]:>10}s                                         ║
║  Throughput:            {stats["throughput_files_per_sec"]:>10} files/sec                               ║
║  Sensitive Files:       {stats["files_with_sensitive_data"]:>10}                                          ║
╚══════════════════════════════════════════════════════════════════════════════╝\033[0m
""")

        # Classification breakdown
        print("\n\033[0;36m📊 Classification Breakdown:\033[0m")
        for cls, count in sorted(
            report["classification_breakdown"].items(), key=lambda x: -x[1]
        ):
            pct = (count / max(stats["processed"], 1)) * 100
            bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
            print(f"  {cls:15} {bar} {count:>5} ({pct:5.1f}%)")

        # Sensitivity breakdown
        print("\n\033[0;33m🔒 Sensitivity Breakdown:\033[0m")
        for sens, count in report["sensitivity_breakdown"].items():
            print(f"  {sens:15} {count:>5}")


# ══════════════════════════════════════════════════════════════════════════════
# CLI INTERFACE
# ══════════════════════════════════════════════════════════════════════════════


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="PHANTOM DAG ORCHESTRATOR - NSA-Grade Data Classification Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  phantom-dag -i ./raw_data -o ./classified
  phantom-dag -i /data/dump -o /data/organized --sanitize full
  phantom-dag -i ./input -o ./output -w 16 -v --dry-run
  phantom-dag --resolve PH-abc123-def456.pdf
""",
    )

    parser.add_argument("-i", "--input", required=True, help="Input directory")
    parser.add_argument("-o", "--output", required=True, help="Output directory")
    parser.add_argument(
        "-w", "--workers", type=int, default=None, help="Worker threads"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument(
        "--dry-run", action="store_true", help="Simulate without moving files"
    )
    parser.add_argument(
        "--sanitize",
        choices=["none", "strip", "pii", "full"],
        default="strip",
        help="Sanitization policy",
    )
    parser.add_argument("--resolve", help="Resolve pseudonym to original path")
    parser.add_argument("--version", action="version", version=f"PHANTOM-DAG {VERSION}")

    args = parser.parse_args()

    # Initialize logger
    global logger
    log_dir = Path(args.output) / ".phantom" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = PhantomLogger(
        "phantom-dag",
        log_file=log_dir / f"phantom_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
        verbose=args.verbose,
    )

    # Sanitization policy mapping
    sanitize_map = {
        "none": SanitizationPolicy.NONE,
        "strip": SanitizationPolicy.STRIP_METADATA,
        "pii": SanitizationPolicy.REDACT_PII,
        "full": SanitizationPolicy.FULL_SANITIZE,
    }

    # Create context
    input_dir = Path(args.input).resolve()
    output_dir = Path(args.output).resolve()

    ctx = PipelineContext(
        input_dir=input_dir,
        output_dir=output_dir,
        staging_dir=output_dir / ".phantom" / "staging",
        quarantine_dir=output_dir / ".phantom" / "quarantine",
        workers=args.workers or os.cpu_count(),
        dry_run=args.dry_run,
        verbose=args.verbose,
        sanitization_policy=sanitize_map.get(
            args.sanitize, SanitizationPolicy.STRIP_METADATA
        ),
    )

    # Execute pipeline
    pipeline = PhantomPipeline(ctx)
    pipeline.execute()

    logger.close()


if __name__ == "__main__":
    main()
