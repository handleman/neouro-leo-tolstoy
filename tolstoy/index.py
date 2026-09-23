"""Index CLI: python -m tolstoy.index build|stats|reset (0008 step 4).

`build` runs clean -> chunk -> embed -> upsert per volume (or `--all`);
`stats` prints collection count + per-volume breakdown; `reset --yes`
drops the collection so a re-index (e.g. after chunk-size retuning)
starts clean.
"""

import argparse
import glob
import os

from tolstoy.config import load_settings
from tolstoy.ingest.chunk import chunk_file
from tolstoy.store import chroma, embed


def _clean_path(clean_dir: str, volume: int) -> str:
    return os.path.join(clean_dir, f"vol{volume:02d}.json")


def build_volume(volume: int, clean_dir: str, batch_size: int = 128) -> int:
    """Chunk, embed and upsert one volume; returns chunks written."""
    settings = load_settings()
    path = _clean_path(clean_dir, volume)
    if not os.path.exists(path):
        print(f"vol{volume:02d}: no clean file at {path}, skipped")
        return 0
    chunks = chunk_file(path, settings.chunk_size, settings.chunk_overlap, settings.chunk_min_chars)
    if not chunks:
        print(f"vol{volume:02d}: 0 work chunks, skipped")
        return 0
    total = 0
    for start in range(0, len(chunks), batch_size):
        batch = chunks[start : start + batch_size]
        vectors = embed.embed([c.text for c in batch])
        chroma.upsert_chunks(batch, vectors)
        total += len(batch)
    print(f"vol{volume:02d}: {total} chunks upserted")
    return total


def build_all(clean_dir: str, only_volume: int | None = None) -> int:
    if only_volume is not None:
        return build_volume(only_volume, clean_dir)
    total = 0
    paths = sorted(glob.glob(os.path.join(clean_dir, "vol*.json")))
    if not paths:
        print(f"no clean files in {clean_dir}")
        return 0
    for path in paths:
        base = os.path.basename(path)
        try:
            volume = int(base[3:5])
        except ValueError:
            print(f"{base}: unparsable volume number, skipped")
            continue
        total += build_volume(volume, clean_dir)
    print(f"total: {total} chunks upserted")
    return total


def show_stats() -> int:
    settings = load_settings()
    try:
        count = chroma.collection_count()
    except Exception as exc:  # empty/missing store reads as zero
        print(f"collection '{settings.collection}': unreachable ({exc})")
        return 0
    print(f"collection '{settings.collection}': {count} chunks")
    for volume, num in chroma.volume_breakdown().items():
        print(f"  vol{volume:02d}: {num}")
    return count


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build/query the tolstoy-ru vector store.")
    parser.add_argument("--clean-dir", default="data/clean")
    sub = parser.add_subparsers(dest="command", required=True)

    build_p = sub.add_parser("build", help="chunk + embed + upsert volumes")
    group = build_p.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true")
    group.add_argument("--volume", type=int, help="volume number, e.g. 4")

    sub.add_parser("stats", help="collection count + per-volume breakdown")

    reset_p = sub.add_parser("reset", help="drop the collection (re-index from scratch)")
    reset_p.add_argument("--yes", action="store_true", required=True)

    args = parser.parse_args(argv)
    if args.command == "build":
        build_all(args.clean_dir, only_volume=None if args.all else args.volume)
        return 0
    if args.command == "stats":
        show_stats()
        return 0
    if args.command == "reset":
        settings = load_settings()
        chroma.reset_collection()
        print(f"collection '{settings.collection}' dropped")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
