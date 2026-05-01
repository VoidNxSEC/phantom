#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEPRECATED: This module is deprecated and will be removed in v3.0.0.
Please use the new modular structure under `phantom.*` instead.

Migration:
    from phantom.core import CortexProcessor
    from phantom.pipeline import FileClassifier, DAGPipeline

See phantom_core/DEPRECATED.md for full migration guide.
"""
import warnings

warnings.warn(
    "phantom_core is deprecated. Use phantom.* modules instead. "
    "See phantom_core/DEPRECATED.md for migration guide.",
    DeprecationWarning,
    stacklevel=2
)

"""
╔══════════════════════════════════════════════════════════════════╗
║  PHANTOM CLASSIFIER v2.0 - NSA-Grade Data Pipeline              ║
║  ─────────────────────────────────────────────────────────────── ║
║  • DAG-based ETL processing                                      ║
║  • BLAKE3/SHA256 integrity verification                          ║
║  • Pseudonymization with reversible mapping                      ║
║  • Intelligent multi-level classification                        ║
║  • Forensic-grade audit trails                                   ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import json
import hashlib
import shutil
import mimetypes
import subprocess
import uuid
import base64
import threading
import queue
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Set, Tuple, Any, Callable
from enum import Enum, auto
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import re
import struct
import tempfile
import time

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION & CONSTANTS
# ═══════════════════════════════════════════════════════════════

VERSION = "2.0.0"
CODENAME = "PHANTOM"

# Classification taxonomy
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

# Sensitivity levels
class Sensitivity(Enum):
    PUBLIC = 0
    INTERNAL = 1
    CONFIDENTIAL = 2
    SECRET = 3
    TOP_SECRET = 4

# File signatures (magic bytes)
MAGIC_SIGNATURES = {
    b'\x89PNG\r\n\x1a\n': ('image/png', Classification.IMAGES),
    b'\xff\xd8\xff': ('image/jpeg', Classification.IMAGES),
    b'GIF87a': ('image/gif', Classification.IMAGES),
    b'GIF89a': ('image/gif', Classification.IMAGES),
    b'%PDF': ('application/pdf', Classification.DOCUMENTS),
    b'PK\x03\x04': ('application/zip', Classification.ARCHIVES),
    b'PK\x05\x06': ('application/zip', Classification.ARCHIVES),
    b'\x1f\x8b': ('application/gzip', Classification.ARCHIVES),
    b'Rar!\x1a\x07': ('application/x-rar', Classification.ARCHIVES),
    b'7z\xbc\xaf\x27\x1c': ('application/x-7z', Classification.ARCHIVES),
    b'\xfd7zXZ\x00': ('application/x-xz', Classification.ARCHIVES),
    b'BZh': ('application/x-bzip2', Classification.ARCHIVES),
    b'\x7fELF': ('application/x-elf', Classification.EXECUTABLES),
    b'MZ': ('application/x-dosexec', Classification.EXECUTABLES),
    b'#!': ('text/x-script', Classification.CODE),
    b'<!DOCTYPE': ('text/html', Classification.CODE),
    b'<?xml': ('text/xml', Classification.DATA),
    b'SQLite format 3': ('application/x-sqlite3', Classification.DATA),
    b'\x00\x00\x00\x1cftyp': ('video/mp4', Classification.VIDEO),
    b'\x00\x00\x00\x20ftyp': ('video/mp4', Classification.VIDEO),
    b'ID3': ('audio/mpeg', Classification.AUDIO),
    b'\xff\xfb': ('audio/mpeg', Classification.AUDIO),
    b'OggS': ('audio/ogg', Classification.AUDIO),
    b'fLaC': ('audio/flac', Classification.AUDIO),
    b'RIFF': ('audio/wav', Classification.AUDIO),
}

# Extension mappings
EXT_CLASSIFICATION = {
    # Documents
    '.pdf': Classification.DOCUMENTS,
    '.doc': Classification.DOCUMENTS,
    '.docx': Classification.DOCUMENTS,
    '.odt': Classification.DOCUMENTS,
    '.rtf': Classification.DOCUMENTS,
    '.txt': Classification.DOCUMENTS,
    '.md': Classification.DOCUMENTS,
    '.tex': Classification.DOCUMENTS,
    '.epub': Classification.DOCUMENTS,
    
    # Images
    '.png': Classification.IMAGES,
    '.jpg': Classification.IMAGES,
    '.jpeg': Classification.IMAGES,
    '.gif': Classification.IMAGES,
    '.bmp': Classification.IMAGES,
    '.tiff': Classification.IMAGES,
    '.webp': Classification.IMAGES,
    '.svg': Classification.IMAGES,
    '.ico': Classification.IMAGES,
    '.raw': Classification.IMAGES,
    '.cr2': Classification.IMAGES,
    '.nef': Classification.IMAGES,
    
    # Audio
    '.mp3': Classification.AUDIO,
    '.wav': Classification.AUDIO,
    '.flac': Classification.AUDIO,
    '.ogg': Classification.AUDIO,
    '.m4a': Classification.AUDIO,
    '.aac': Classification.AUDIO,
    '.wma': Classification.AUDIO,
    
    # Video
    '.mp4': Classification.VIDEO,
    '.mkv': Classification.VIDEO,
    '.avi': Classification.VIDEO,
    '.mov': Classification.VIDEO,
    '.wmv': Classification.VIDEO,
    '.webm': Classification.VIDEO,
    '.flv': Classification.VIDEO,
    
    # Code
    '.py': Classification.CODE,
    '.js': Classification.CODE,
    '.ts': Classification.CODE,
    '.jsx': Classification.CODE,
    '.tsx': Classification.CODE,
    '.rs': Classification.CODE,
    '.go': Classification.CODE,
    '.c': Classification.CODE,
    '.cpp': Classification.CODE,
    '.h': Classification.CODE,
    '.java': Classification.CODE,
    '.rb': Classification.CODE,
    '.php': Classification.CODE,
    '.sh': Classification.CODE,
    '.bash': Classification.CODE,
    '.zsh': Classification.CODE,
    '.fish': Classification.CODE,
    '.ps1': Classification.CODE,
    '.nix': Classification.CODE,
    '.hs': Classification.CODE,
    '.ml': Classification.CODE,
    '.scala': Classification.CODE,
    '.kt': Classification.CODE,
    '.swift': Classification.CODE,
    '.r': Classification.CODE,
    '.sql': Classification.CODE,
    '.lua': Classification.CODE,
    '.pl': Classification.CODE,
    '.html': Classification.CODE,
    '.css': Classification.CODE,
    '.scss': Classification.CODE,
    '.less': Classification.CODE,
    
    # Data
    '.json': Classification.DATA,
    '.xml': Classification.DATA,
    '.yaml': Classification.DATA,
    '.yml': Classification.DATA,
    '.toml': Classification.DATA,
    '.csv': Classification.DATA,
    '.tsv': Classification.DATA,
    '.parquet': Classification.DATA,
    '.avro': Classification.DATA,
    '.db': Classification.DATA,
    '.sqlite': Classification.DATA,
    '.sqlite3': Classification.DATA,
    
    # Archives
    '.zip': Classification.ARCHIVES,
    '.tar': Classification.ARCHIVES,
    '.gz': Classification.ARCHIVES,
    '.bz2': Classification.ARCHIVES,
    '.xz': Classification.ARCHIVES,
    '.7z': Classification.ARCHIVES,
    '.rar': Classification.ARCHIVES,
    '.zst': Classification.ARCHIVES,
    
    # Configs
    '.conf': Classification.CONFIGS,
    '.cfg': Classification.CONFIGS,
    '.ini': Classification.CONFIGS,
    '.env': Classification.CONFIGS,
    '.properties': Classification.CONFIGS,
    
    # Logs
    '.log': Classification.LOGS,
    '.out': Classification.LOGS,
    '.err': Classification.LOGS,
    
    # Crypto
    '.pem': Classification.CRYPTO,
    '.crt': Classification.CRYPTO,
    '.key': Classification.CRYPTO,
    '.pub': Classification.CRYPTO,
    '.gpg': Classification.CRYPTO,
    '.asc': Classification.CRYPTO,
    '.p12': Classification.CRYPTO,
    '.pfx': Classification.CRYPTO,
    '.jks': Classification.CRYPTO,
    '.keystore': Classification.CRYPTO,
}

# Sensitive patterns (regex)
SENSITIVE_PATTERNS = [
    (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 'email'),
    (r'\b(?:\d{3}[-.]?)?\d{3}[-.]?\d{4}\b', 'phone'),
    (r'\b\d{3}[-.]?\d{2}[-.]?\d{4}\b', 'ssn'),
    (r'\b(?:\d{4}[-\s]?){3}\d{4}\b', 'credit_card'),
    (r'\b[A-Za-z0-9]{32,}\b', 'api_key'),
    (r'(?i)(password|passwd|pwd|secret|token|api[_-]?key)\s*[=:]\s*["\\]?[^\s"\\]+', 'credential'),
    (r'\b(?:\d{1,3}\.){3}\d{1,3}\b', 'ipv4'),
    (r'\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b', 'uuid'),
    (r'-----BEGIN (?:RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----', 'private_key'),
    (r'-----BEGIN CERTIFICATE-----', 'certificate'),
    (r'(?i)cpf\s*[=:]\s*\d{3}\.?\d{3}\.?\d{3}-?\d{2}', 'cpf_br'),
    (r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b', 'cpf_br_raw'),
]

# ═══════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════

@dataclass
class FileFingerprint:
    """Immutable file fingerprint for integrity verification"""
    sha256: str
    blake3: str
    size: int
    created_at: str
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'FileFingerprint':
        return cls(**data)

@dataclass
class FileMetadata:
    """Complete file metadata container"""
    original_path: str
    original_name: str
    pseudonym: str
    classification: str
    sensitivity: int
    mime_type: str
    extension: str
    size: int
    fingerprint: FileFingerprint
    metadata: Dict = field(default_factory=dict)
    sensitive_findings: List[Dict] = field(default_factory=list)
    tags: Set[str] = field(default_factory=set)
    processed_at: str = ""
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d['tags'] = list(self.tags)
        d['fingerprint'] = self.fingerprint.to_dict()
        return d

@dataclass 
class PipelineStats:
    """Pipeline execution statistics"""
    total_files: int = 0
    processed: int = 0
    failed: int = 0
    skipped: int = 0
    total_size: int = 0
    by_classification: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    by_sensitivity: Dict[int, int] = field(default_factory=lambda: defaultdict(int))
    by_extension: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    errors: List[Dict] = field(default_factory=list)
    start_time: float = 0
    end_time: float = 0
    
    @property
    def duration(self) -> float:
        return self.end_time - self.start_time
    
    @property
    def success_rate(self) -> float:
        if self.total_files == 0:
            return 0.0
        return (self.processed / self.total_files) * 100

@dataclass
class DAGNode:
    """DAG pipeline node"""
    name: str
    func: Callable
    dependencies: List[str] = field(default_factory=list)
    completed: bool = False
    result: Any = None
    error: Optional[str] = None

# ═══════════════════════════════════════════════════════════════
# CORE ENGINE
# ═══════════════════════════════════════════════════════════════

class PhantomClassifier:
    """Main classification engine"""
    
    def __init__(self, 
                 input_dir: str,
                 output_dir: str,
                 pseudonym_map_path: str = None,
                 workers: int = None,
                 dry_run: bool = False,
                 verbose: bool = False):
        
        self.input_dir = Path(input_dir).resolve()
        self.output_dir = Path(output_dir).resolve()
        self.pseudonym_map_path = Path(pseudonym_map_path) if pseudonym_map_path else self.output_dir / ".phantom_map.json"
        self.workers = workers or os.cpu_count()
        self.dry_run = dry_run
        self.verbose = verbose
        
        # State
        self.pseudonym_map: Dict[str, str] = {}
        self.reverse_map: Dict[str, str] = {}
        self.processed_files: Dict[str, FileMetadata] = {}
        self.stats = PipelineStats()
        
        # Thread-safe counters
        self._lock = threading.Lock()
        self._progress_queue = queue.Queue()
        
        # Initialize
        self._init_directories()
        self._load_pseudonym_map()
    
    def _init_directories(self):
        """Initialize output directory structure"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create classification directories
        for cls in Classification:
            (self.output_dir / cls.value).mkdir(exist_ok=True)
        
        # Create metadata directory
        (self.output_dir / ".phantom").mkdir(exist_ok=True)
        (self.output_dir / ".phantom" / "reports").mkdir(exist_ok=True)
        (self.output_dir / ".phantom" / "logs").mkdir(exist_ok=True)
    
    def _load_pseudonym_map(self):
        """Load existing pseudonym mappings"""
        if self.pseudonym_map_path.exists():
            with open(self.pseudonym_map_path, 'r') as f:
                data = json.load(f)
                self.pseudonym_map = data.get('pseudonyms', {})
                self.reverse_map = {v: k for k, v in self.pseudonym_map.items()}
                self._log(f"Loaded {len(self.pseudonym_map)} existing pseudonyms")
    
    def _save_pseudonym_map(self):
        """Persist pseudonym mappings"""
        data = {
            'version': VERSION,
            'created': datetime.now(timezone.utc).isoformat(),
            'pseudonyms': self.pseudonym_map,
            'stats': {
                'total_mappings': len(self.pseudonym_map)
            }
        }
        with open(self.pseudonym_map_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _log(self, msg: str, level: str = "INFO"):
        """Thread-safe logging"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        colors = {
            "INFO": "\033[0;36m",     # Cyan
            "WARN": "\033[0;33m",     # Yellow
            "ERROR": "\033[0;31m",    # Red
            "SUCCESS": "\033[0;32m",  # Green
            "DEBUG": "\033[0;35m",    # Magenta
        }
        color = colors.get(level, "\033[0m")
        reset = "\033[0m"
        
        if self.verbose or level in ("ERROR", "WARN", "SUCCESS"):
            print(f"{color}[{timestamp}] [{level}] {msg}{reset}")
    
    # ═══════════════════════════════════════════════════════════════
    # HASHING & INTEGRITY
    # ═══════════════════════════════════════════════════════════════
    
    def compute_fingerprint(self, filepath: Path) -> FileFingerprint:
        """Compute file fingerprint with multiple hash algorithms"""
        sha256_hash = hashlib.sha256()
        blake3_hash = hashlib.blake2b()  # Using blake2b as fallback
        
        # Try to use b3sum for BLAKE3 if available
        try:
            result = subprocess.run(
                ['b3sum', '--no-names', str(filepath)],
                capture_output=True, text=True, timeout=60
            )
            blake3_hex = result.stdout.strip() if result.returncode == 0 else None
        except:
            blake3_hex = None
        
        # Compute SHA256 and fallback BLAKE2b
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                sha256_hash.update(chunk)
                if not blake3_hex:
                    blake3_hash.update(chunk)
        
        stat = filepath.stat()
        
        return FileFingerprint(
            sha256=sha256_hash.hexdigest(),
            blake3=blake3_hex or blake3_hash.hexdigest(),
            size=stat.st_size,
            created_at=datetime.now(timezone.utc).isoformat()
        )
    
    def verify_integrity(self, filepath: Path, fingerprint: FileFingerprint) -> bool:
        """Verify file integrity against stored fingerprint"""
        current = self.compute_fingerprint(filepath)
        return (current.sha256 == fingerprint.sha256 and 
                current.size == fingerprint.size)
    
    # ═══════════════════════════════════════════════════════════════
    # PSEUDONYMIZATION
    # ═══════════════════════════════════════════════════════════════
    
    def generate_pseudonym(self, original_path: str, extension: str) -> str:
        """Generate deterministic pseudonym for file"""
        # Check if already mapped
        if original_path in self.reverse_map:
            return self.reverse_map[original_path]
        
        # Generate new pseudonym
        # Format: PH-<timestamp_hex>-<random_hex>.<ext>
        timestamp_hex = hex(int(time.time() * 1000))[-8:]
        random_hex = uuid.uuid4().hex[:8]
        pseudonym = f"PH-{timestamp_hex}-{random_hex}{extension}"
        
        # Store bidirectional mapping
        with self._lock:
            self.pseudonym_map[pseudonym] = original_path
            self.reverse_map[original_path] = pseudonym
        
        return pseudonym
    
    def resolve_pseudonym(self, pseudonym: str) -> Optional[str]:
        """Resolve pseudonym back to original path"""
        return self.pseudonym_map.get(pseudonym)
    
    # ═══════════════════════════════════════════════════════════════
    # CLASSIFICATION ENGINE
    # ═══════════════════════════════════════════════════════════════
    
    def detect_by_magic(self, filepath: Path) -> Tuple[Optional[str], Optional[Classification]]:
        """Detect file type by magic bytes"""
        try:
            with open(filepath, 'rb') as f:
                header = f.read(32)
            
            for magic, (mime, cls) in MAGIC_SIGNATURES.items():
                if header.startswith(magic):
                    return mime, cls
        except:
            pass
        return None, None
    
    def detect_by_extension(self, filepath: Path) -> Tuple[Optional[str], Optional[Classification]]:
        """Detect file type by extension"""
        ext = filepath.suffix.lower()
        cls = EXT_CLASSIFICATION.get(ext, Classification.UNKNOWN)
        mime = mimetypes.guess_type(str(filepath))[0]
        return mime, cls
    
    def detect_sensitive_content(self, filepath: Path, max_bytes: int = 1048576) -> List[Dict]:
        """Scan file content for sensitive patterns"""
        findings = []
        
        try:
            # Only scan text-like files
            with open(filepath, 'rb') as f:
                raw = f.read(max_bytes)
            
            # Try to decode as text
            try:
                content = raw.decode('utf-8')
            except:
                try:
                    content = raw.decode('latin-1')
                except:
                    return findings
            
            # Scan for patterns
            for pattern, pattern_name in SENSITIVE_PATTERNS:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    findings.append({
                        'type': pattern_name,
                        'count': len(matches),
                        'samples': matches[:3]  # First 3 samples
                    })
        except Exception as e:
            self._log(f"Sensitive scan error: {e}", "DEBUG")
        
        return findings
    
    def classify_file(self, filepath: Path) -> Tuple[Classification, str, int]:
        """
        Multi-level classification:
        1. Magic bytes detection
        2. Extension fallback
        3. Content analysis
        """
        # Level 1: Magic bytes
        mime_magic, cls_magic = self.detect_by_magic(filepath)
        
        # Level 2: Extension
        mime_ext, cls_ext = self.detect_by_extension(filepath)
        
        # Prioritize magic detection
        classification = cls_magic or cls_ext or Classification.UNKNOWN
        mime_type = mime_magic or mime_ext or "application/octet-stream"
        
        # Determine sensitivity
        sensitivity = Sensitivity.PUBLIC.value
        
        # Check for crypto files
        if classification == Classification.CRYPTO:
            sensitivity = Sensitivity.SECRET.value
        
        # Check extension patterns
        ext = filepath.suffix.lower()
        if ext in ('.key', '.pem', '.p12', '.pfx'):
            sensitivity = Sensitivity.TOP_SECRET.value
        elif ext in ('.env', '.credentials'):
            sensitivity = Sensitivity.CONFIDENTIAL.value
        
        return classification, mime_type, sensitivity
    
    # ═══════════════════════════════════════════════════════════════
    # FILE PROCESSING
    # ═══════════════════════════════════════════════════════════════
    
    def process_file(self, filepath: Path) -> Optional[FileMetadata]:
        """Process single file through classification pipeline"""
        try:
            # Skip if already processed
            str_path = str(filepath)
            if str_path in self.reverse_map:
                self._log(f"Skipping already processed: {filepath.name}", "DEBUG")
                return None
            
            # Compute fingerprint BEFORE any operation
            fingerprint = self.compute_fingerprint(filepath)
            
            # Classify
            classification, mime_type, sensitivity = self.classify_file(filepath)
            
            # Generate pseudonym
            pseudonym = self.generate_pseudonym(str_path, filepath.suffix.lower())
            
            # Scan for sensitive content
            sensitive_findings = []
            if classification in (Classification.DOCUMENTS, Classification.CODE, 
                                  Classification.CONFIGS, Classification.DATA,
                                  Classification.LOGS):
                sensitive_findings = self.detect_sensitive_content(filepath)
                if sensitive_findings:
                    sensitivity = max(sensitivity, Sensitivity.CONFIDENTIAL.value)
            
            # Build metadata
            metadata = FileMetadata(
                original_path=str_path,
                original_name=filepath.name,
                pseudonym=pseudonym,
                classification=classification.value,
                sensitivity=sensitivity,
                mime_type=mime_type,
                extension=filepath.suffix.lower(),
                size=fingerprint.size,
                fingerprint=fingerprint,
                sensitive_findings=sensitive_findings,
                tags=set(),
                processed_at=datetime.now(timezone.utc).isoformat()
            )
            
            # Add auto-tags
            if sensitive_findings:
                metadata.tags.add("has_sensitive_data")
            if fingerprint.size > 100 * 1024 * 1024:  # >100MB
                metadata.tags.add("large_file")
            if filepath.name.startswith('.'):
                metadata.tags.add("hidden")
            
            # Determine destination
            dest_dir = self.output_dir / classification.value
            dest_path = dest_dir / pseudonym
            
            # Execute move (or copy)
            if not self.dry_run:
                shutil.copy2(filepath, dest_path)
                
                # Verify integrity after copy
                if not self.verify_integrity(dest_path, fingerprint):
                    self._log(f"INTEGRITY FAILURE: {filepath.name}", "ERROR")
                    dest_path.unlink()
                    raise ValueError("Integrity verification failed")
            
            # Update stats
            with self._lock:
                self.stats.processed += 1
                self.stats.total_size += fingerprint.size
                self.stats.by_classification[classification.value] += 1
                self.stats.by_sensitivity[sensitivity] += 1
                self.stats.by_extension[filepath.suffix.lower()] += 1
                self.processed_files[pseudonym] = metadata
            
            self._log(f"✓ {filepath.name} → {classification.value}/{pseudonym}", "SUCCESS")
            return metadata
            
        except Exception as e:
            with self._lock:
                self.stats.failed += 1
                self.stats.errors.append({
                    'file': str(filepath),
                    'error': str(e),
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
            self._log(f"✗ {filepath.name}: {e}", "ERROR")
            return None
    
    # ═══════════════════════════════════════════════════════════════
    # DAG PIPELINE EXECUTION
    # ═══════════════════════════════════════════════════════════════
    
    def discover_files(self) -> List[Path]:
        """Discover all files in input directory"""
        files = []
        for item in self.input_dir.rglob('*'):
            if item.is_file() and not item.name.startswith('.phantom'):
                files.append(item)
        return files
    
    def run_parallel(self, files: List[Path]):
        """Execute parallel file processing"""
        self._log(f"Processing {len(files)} files with {self.workers} workers")
        
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {executor.submit(self.process_file, f): f for f in files}
            
            for future in as_completed(futures):
                filepath = futures[future]
                try:
                    result = future.result()
                except Exception as e:
                    self._log(f"Worker exception for {filepath}: {e}", "ERROR")
    
    def generate_report(self) -> Dict:
        """Generate comprehensive pipeline report"""
        report = {
            'phantom_version': VERSION,
            'codename': CODENAME,
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'pipeline': {
                'input_directory': str(self.input_dir),
                'output_directory': str(self.output_dir),
                'dry_run': self.dry_run,
                'workers': self.workers
            },
            'statistics': {
                'total_files': self.stats.total_files,
                'processed': self.stats.processed,
                'failed': self.stats.failed,
                'skipped': self.stats.skipped,
                'success_rate': f"{self.stats.success_rate:.2f}%",
                'total_size_bytes': self.stats.total_size,
                'total_size_human': self._human_size(self.stats.total_size),
                'duration_seconds': f"{self.stats.duration:.2f}",
                'files_per_second': f"{self.stats.processed / max(self.stats.duration, 0.001):.2f}"
            },
            'classification_breakdown': dict(self.stats.by_classification),
            'sensitivity_breakdown': {
                Sensitivity(k).name: v for k, v in self.stats.by_sensitivity.items()
            },
            'extension_breakdown': dict(self.stats.by_extension),
            'errors': self.stats.errors,
            'processed_files': {
                k: v.to_dict() for k, v in self.processed_files.items()
            }
        }
        return report
    
    def _human_size(self, size: int) -> str:
        """Convert bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} PB"
    
    # ═══════════════════════════════════════════════════════════════
    # MAIN EXECUTION
    # ═══════════════════════════════════════════════════════════════
    
    def execute(self):
        """Execute full classification pipeline"""
        self._print_banner()
        
        self.stats.start_time = time.time()
        
        # Stage 1: Discovery
        self._log("═══ STAGE 1: FILE DISCOVERY ═══", "INFO")
        files = self.discover_files()
        self.stats.total_files = len(files)
        self._log(f"Discovered {len(files)} files", "INFO")
        
        if not files:
            self._log("No files to process", "WARN")
            return
        
        # Stage 2: Classification & Processing
        self._log("═══ STAGE 2: CLASSIFICATION ═══", "INFO")
        self.run_parallel(files)
        
        # Stage 3: Persistence
        self._log("═══ STAGE 3: PERSISTENCE ═══", "INFO")
        self._save_pseudonym_map()
        
        self.stats.end_time = time.time()
        
        # Stage 4: Reporting
        self._log("═══ STAGE 4: REPORT GENERATION ═══", "INFO")
        report = self.generate_report()
        
        # Save report
        report_path = self.output_dir / ".phantom" / "reports" / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        self._log(f"Report saved: {report_path}", "SUCCESS")
        
        # Print summary
        self._print_summary(report)
    
    def _print_banner(self):
        """Print startup banner"""
        banner = f"""
\033[0;35m╔══════════════════════════════════════════════════════════════════╗
║  ██████╗ ██╗  ██╗ █████╗ ███╗   ██╗████████╗ ██████╗ ███╗   ███╗ 
║  ██╔══██╗██║  ██║██╔══██╗████╗  ██║╚══██╔══╝██╔═══██╗████╗ ████║ 
║  ██████╔╝███████║███████║██╔██╗ ██║   ██║   ██║   ██║██╔████╔██║ 
║  ██╔═══╝ ██╔══██║██╔══██║██║╚██╗██║   ██║   ██║   ██║██║╚██╔╝██║ 
║  ██║     ██║  ██║██║  ██║██║ ╚████║   ██║   ╚██████╔╝██║ ╚═╝ ██║ 
║  ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝    ╚═════╝ ╚═╝     ╚═╝ 
║  CLASSIFIER v{VERSION}                                              ║
╚══════════════════════════════════════════════════════════════════╝\033[0m
"""
        print(banner)
    
    def _print_summary(self, report: Dict):
        """Print execution summary"""
        stats = report['statistics']
        print(f"""
\033[0;32m╔══════════════════════════════════════════════════════════════════╗
║                      EXECUTION SUMMARY                            ║
╠══════════════════════════════════════════════════════════════════╣
║  Total Files:      {stats['total_files']:>10}                                  ║
║  Processed:        {stats['processed']:>10}                                  ║
║  Failed:           {stats['failed']:>10}                                  ║
║  Success Rate:     {stats['success_rate']:>10}                                  ║
║  Total Size:       {stats['total_size_human']:>10}                                  ║
║  Duration:         {stats['duration_seconds']:>10}s                                 ║
║  Throughput:       {stats['files_per_second']:>10} files/sec                       ║
╚══════════════════════════════════════════════════════════════════╝\033[0m
""")
        
        # Classification breakdown
        print("\n\033[0;36m📊 Classification Breakdown:\033[0m")
        for cls, count in sorted(report['classification_breakdown'].items(), key=lambda x: -x[1]):
            pct = (count / max(stats['processed'], 1)) * 100
            bar = '█' * int(pct / 5) + '░' * (20 - int(pct / 5))
            print(f"  {cls:15} {bar} {count:>5} ({pct:5.1f}%)")
        
        # Sensitivity breakdown
        print("\n\033[0;33m🔒 Sensitivity Breakdown:\033[0m")
        for sens, count in sorted(report['sensitivity_breakdown'].items()):
            print(f"  {sens:15} {count:>5}")

# ═══════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='PHANTOM CLASSIFIER - NSA-Grade Data Classification Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  phantom -i ./raw_data -o ./classified
  phantom -i /data/dump -o /data/organized --dry-run
  phantom -i ./input -o ./output -w 16 -v
  phantom --resolve PH-abc123-def456.pdf
'''
    )
    
    parser.add_argument('-i', '--input', required=True, help='Input directory')
    parser.add_argument('-o', '--output', required=True, help='Output directory')
    parser.add_argument('-w', '--workers', type=int, default=None, help='Worker threads')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--dry-run', action='store_true', help='Simulate without moving files')
    parser.add_argument('--resolve', help='Resolve pseudonym to original path')
    parser.add_argument('--verify', help='Verify file integrity')
    parser.add_argument('--version', action='version', version=f'PHANTOM {VERSION}')
    
    args = parser.parse_args()
    
    # Handle resolve command
    if args.resolve:
        classifier = PhantomClassifier(args.input, args.output)
        original = classifier.resolve_pseudonym(args.resolve)
        if original:
            print(f"Original: {original}")
        else:
            print("Pseudonym not found in map")
        return
    
    # Main execution
    classifier = PhantomClassifier(
        input_dir=args.input,
        output_dir=args.output,
        workers=args.workers,
        dry_run=args.dry_run,
        verbose=args.verbose
    )
    classifier.execute()

if __name__ == '__main__':
    main()
