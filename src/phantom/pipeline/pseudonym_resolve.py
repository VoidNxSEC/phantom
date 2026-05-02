"""
Resolve pseudonyms back to original paths using `.phantom/pseudonym_map.json`
(and optional SQLite `phantom.db`) for chain-of-custody / integrity checks.

This is the inverse of pseudonymization: recover lineage without exposing identities
until an authorized resolver step runs against the persisted map.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

DEFAULT_MAP_RELATIVE = Path(".phantom") / "pseudonym_map.json"
DEFAULT_DB_RELATIVE = Path(".phantom") / "phantom.db"


def default_map_path(output_dir: Path) -> Path:
    return output_dir / DEFAULT_MAP_RELATIVE


def load_pseudonym_map(map_path: Path) -> dict[str, str]:
    """Load `pseudonym -> original_path` from JSON written by the DAG."""
    if not map_path.is_file():
        raise FileNotFoundError(f"Pseudonym map not found: {map_path}")
    with open(map_path, encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
    mappings = data.get("mappings")
    if not isinstance(mappings, dict):
        raise ValueError(f"Invalid pseudonym map format (missing 'mappings'): {map_path}")
    out: dict[str, str] = {}
    for k, v in mappings.items():
        if isinstance(k, str) and isinstance(v, str):
            out[k] = v
    return out


def resolve_pseudonym(mappings: dict[str, str], pseudonym: str) -> str | None:
    """Return original path for a pseudonym filename, or None if unknown."""
    if pseudonym in mappings:
        return mappings[pseudonym]
    base = Path(pseudonym).name
    if base in mappings:
        return mappings[base]
    return None


def _record_metadata_for_pseudonym(db_path: Path, pseudonym: str) -> dict[str, Any] | None:
    if not db_path.is_file():
        return None
    key = Path(pseudonym).name
    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT metadata FROM file_records WHERE pseudonym = ?",
            (key,),
        )
        row = cur.fetchone()
        if row and row[0]:
            return json.loads(row[0])
    finally:
        conn.close()
    return None


def verify_output_integrity(output_dir: Path, pseudonym: str) -> tuple[bool, str]:
    """
    Verify the processed file at `destination_path` against `fingerprint_output`
    stored in SQLite metadata. Returns (ok, message).
    """
    from phantom.pipeline.phantom_dag import CryptoEngine, FileFingerprint

    db_path = output_dir / DEFAULT_DB_RELATIVE
    meta = _record_metadata_for_pseudonym(db_path, pseudonym)
    if not meta:
        return False, f"No database record for pseudonym {pseudonym!r} (expected {db_path})"

    dest = meta.get("destination_path") or ""
    fp_out = meta.get("fingerprint_output")
    if not dest:
        return False, "Record has no destination_path"
    if not fp_out:
        return False, "Record has no fingerprint_output (run pipeline with verification enabled)"

    path = Path(dest)
    if not path.is_file():
        return False, f"Output file missing: {path}"

    expected = FileFingerprint(
        sha256=fp_out["sha256"],
        blake3=fp_out["blake3"],
        xxhash=fp_out.get("xxhash", ""),
        size=int(fp_out["size"]),
        created_at=fp_out.get("created_at", ""),
        nonce=fp_out.get("nonce", ""),
    )
    ok = CryptoEngine.verify_integrity(path, expected)
    if ok:
        return True, f"Integrity OK: {path}"
    return False, f"Integrity mismatch for {path} (expected SHA256 {expected.sha256[:16]}…)"


def format_resolve_result(
    output_dir: Path,
    pseudonym: str,
    *,
    verify: bool,
    map_path: Path | None = None,
) -> tuple[int, str]:
    """Returns (exit_code, text for stdout)."""
    path_map = map_path or default_map_path(output_dir)
    try:
        mappings = load_pseudonym_map(path_map)
    except (OSError, ValueError) as exc:
        return 2, str(exc)

    original = resolve_pseudonym(mappings, pseudonym)
    if original is None:
        return 1, f"Unknown pseudonym: {pseudonym!r}"

    lines = [
        f"Pseudonym:  {Path(pseudonym).name}",
        f"Original:   {original}",
        f"Map file:   {path_map}",
    ]
    if verify:
        ok, msg = verify_output_integrity(output_dir, pseudonym)
        lines.append(f"Verify:     {msg}")
        return (0 if ok else 2), "\n".join(lines)
    return 0, "\n".join(lines)
