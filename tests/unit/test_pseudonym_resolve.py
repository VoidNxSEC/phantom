"""Tests for pseudonym → original path resolution (integrity / custody)."""

import json
from pathlib import Path

import pytest

from phantom.pipeline.pseudonym_resolve import (
    format_resolve_result,
    load_pseudonym_map,
    resolve_pseudonym,
)


def test_load_and_resolve_roundtrip(tmp_path: Path) -> None:
    map_path = tmp_path / ".phantom" / "pseudonym_map.json"
    map_path.parent.mkdir(parents=True)
    mappings = {"PH-a-b-c.pdf": "/secret/original/report.pdf"}
    map_path.write_text(
        json.dumps({"version": "1", "mappings": mappings}),
        encoding="utf-8",
    )

    loaded = load_pseudonym_map(map_path)
    assert loaded["PH-a-b-c.pdf"] == "/secret/original/report.pdf"
    assert resolve_pseudonym(loaded, "PH-a-b-c.pdf") == "/secret/original/report.pdf"


def test_format_resolve_result_ok(tmp_path: Path) -> None:
    map_path = tmp_path / ".phantom" / "pseudonym_map.json"
    map_path.parent.mkdir(parents=True)
    map_path.write_text(
        json.dumps(
            {
                "mappings": {"PH-x-y-z.txt": "/home/user/doc.txt"},
            }
        ),
        encoding="utf-8",
    )

    code, text = format_resolve_result(
        tmp_path,
        "PH-x-y-z.txt",
        verify=False,
    )
    assert code == 0
    assert "/home/user/doc.txt" in text


def test_format_resolve_unknown(tmp_path: Path) -> None:
    map_path = tmp_path / ".phantom" / "pseudonym_map.json"
    map_path.parent.mkdir(parents=True)
    map_path.write_text(json.dumps({"mappings": {}}), encoding="utf-8")

    code, text = format_resolve_result(tmp_path, "missing.bin", verify=False)
    assert code == 1
    assert "Unknown" in text


def test_load_invalid_map(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="mappings"):
        load_pseudonym_map(bad)
