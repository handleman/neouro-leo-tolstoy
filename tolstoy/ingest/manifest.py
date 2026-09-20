"""Manifest builder: versioned corpus record (0002 contract).

`build` scans data/raw/, cleans every volume, writes data/clean/*.json
and data/manifest.json (the sole committed data artifact). `verify`
re-hashes the raws and reports drift; changed SHA means re-ingest.
"""

import argparse
import datetime
import hashlib
import json
import os
import sys

from tolstoy.ingest import epub as epub_reader
from tolstoy.ingest.clean import (
    clean_volume,
    section_count,
    work_list,
    work_word_count,
    write_clean_json,
)


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tool_versions() -> dict:
    versions = {"python": sys.version.split()[0]}
    for package in ("ebooklib", "lxml"):
        try:
            module = __import__(package)
            versions[package] = getattr(module, "__version__", "unknown")
        except ImportError:
            versions[package] = "missing"
    return versions


def build_manifest(raw_dir: str, clean_dir: str, out_path: str) -> dict:
    volumes = []
    for filename in sorted(os.listdir(raw_dir)):
        if not filename.lower().endswith(".epub"):
            continue
        raw_path = os.path.join(raw_dir, filename)
        raw = epub_reader.read_volume(raw_path)
        clean = clean_volume(raw)
        write_clean_json(clean, clean_dir)
        titles = raw.titles
        volumes.append(
            {
                "volume": clean.volume_no,
                "filename": filename,
                "title": titles[0] if titles else "",
                "series": titles[1] if len(titles) > 1 else "",
                "creator": clean.creator,
                "publisher": clean.publisher,
                "pub_year": clean.pub_year,
                "language": clean.language or "ru",
                "sha256": sha256_file(raw_path),
                "byte_size": os.path.getsize(raw_path),
                "section_count": section_count(clean),
                "work_list": work_list(clean),
                "word_count": work_word_count(clean),
                "license": "public-domain",
                "source_note": "local 22-vol edition (Художественная литература)",
            }
        )
    manifest = {
        "generated_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "tool_versions": tool_versions(),
        "volumes": volumes,
    }
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=1, sort_keys=True)
        handle.write("\n")
    return manifest


def verify_manifest(manifest_path: str, raw_dir: str) -> tuple[bool, list[str]]:
    """Re-hash raws and compare. Returns (ok, problems)."""
    with open(manifest_path, encoding="utf-8") as handle:
        manifest = json.load(handle)
    problems = []
    seen = set()
    for entry in manifest.get("volumes", []):
        filename = entry["filename"]
        seen.add(filename)
        raw_path = os.path.join(raw_dir, filename)
        if not os.path.exists(raw_path):
            problems.append(f"missing raw file: {filename}")
            continue
        actual = sha256_file(raw_path)
        if actual != entry["sha256"]:
            problems.append(f"SHA drift: {filename}")
    for filename in sorted(os.listdir(raw_dir)):
        if filename.lower().endswith(".epub") and filename not in seen:
            problems.append(f"unmanifested raw file: {filename}")
    return (len(problems) == 0, problems)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build or verify data/manifest.json.")
    parser.add_argument("--raw", default="data/raw")
    parser.add_argument("--clean", default="data/clean")
    parser.add_argument("--manifest", default="data/manifest.json")
    parser.add_argument("command", choices=("build", "verify"))
    args = parser.parse_args(argv)

    if args.command == "build":
        manifest = build_manifest(args.raw, args.clean, args.manifest)
        total_words = sum(volume["word_count"] for volume in manifest["volumes"])
        print(
            f"manifest: {len(manifest['volumes'])} volumes, "
            f"{total_words} work words -> {args.manifest}"
        )
        return 0

    ok, problems = verify_manifest(args.manifest, args.raw)
    for problem in problems:
        print(problem)
    print("verify: OK" if ok else f"verify: {len(problems)} problem(s)")
    return 0 if ok else 1
