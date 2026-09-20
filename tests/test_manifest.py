"""Manifest tests: build fields, verify, drift, determinism."""

import json
import os
import shutil

import pytest

from tolstoy.ingest.manifest import build_manifest, verify_manifest

VOL1 = os.path.join("data/raw", "Толстой Л.Н-Том 1..epub")
needs_vol1 = pytest.mark.skipif(not os.path.exists(VOL1), reason="local Vol. 1 EPUB not present")


@needs_vol1
def test_build_entry_fields(tmp_path) -> None:
    raw_dir = str(tmp_path / "raw")
    os.makedirs(raw_dir)
    shutil.copy(VOL1, raw_dir)
    manifest = build_manifest(raw_dir, str(tmp_path / "clean"), str(tmp_path / "manifest.json"))
    assert len(manifest["volumes"]) == 1
    entry = manifest["volumes"][0]
    assert entry["volume"] == 1
    assert entry["language"] == "ru"
    assert entry["license"] == "public-domain"
    assert len(entry["sha256"]) == 64
    assert entry["byte_size"] > 0
    assert entry["section_count"] > 0
    assert "Детство" in entry["work_list"]
    assert entry["word_count"] > 1000


@needs_vol1
def test_verify_ok_then_drift(tmp_path) -> None:
    raw_dir = str(tmp_path / "raw")
    os.makedirs(raw_dir)
    target = os.path.join(raw_dir, os.path.basename(VOL1))
    shutil.copy(VOL1, target)
    manifest_path = str(tmp_path / "manifest.json")
    build_manifest(raw_dir, str(tmp_path / "clean"), manifest_path)

    ok, problems = verify_manifest(manifest_path, raw_dir)
    assert ok and problems == []

    with open(target, "ab") as handle:  # tamper
        handle.write(b"\x00")
    ok, problems = verify_manifest(manifest_path, raw_dir)
    assert not ok and any("SHA drift" in problem for problem in problems)


@needs_vol1
def test_rebuild_payload_deterministic(tmp_path) -> None:
    raw_dir = str(tmp_path / "raw")
    os.makedirs(raw_dir)
    shutil.copy(VOL1, raw_dir)
    first = build_manifest(raw_dir, str(tmp_path / "clean"), str(tmp_path / "m1.json"))
    second = build_manifest(raw_dir, str(tmp_path / "clean"), str(tmp_path / "m2.json"))
    assert first["volumes"] == second["volumes"]  # only generated_at may differ
    with open(tmp_path / "m1.json", encoding="utf-8") as handle:
        assert json.load(handle)["volumes"] == second["volumes"]
