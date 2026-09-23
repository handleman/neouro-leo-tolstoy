"""Search REPL: embed -> query -> print top-k (0008 step 6).

Learning surface for chunk/overlap/cosine intuition (run before any LLM
exists). Filters: repeatable `--filter work=<name>` / `--filter
volume=<NN>`. Empty line re-prompts; `quit`/`exit`/Ctrl-D leaves.
"""

import argparse

from tolstoy.config import load_settings
from tolstoy.store import chroma, embed


def parse_filters(pairs: list[str]) -> dict:
    search_filter: dict = {}
    for pair in pairs:
        if "=" not in pair:
            raise ValueError(f"bad --filter {pair!r}, expected key=value")
        key, value = pair.split("=", 1)
        key, value = key.strip(), value.strip()
        if key == "volume":
            search_filter["volume"] = int(value)
        elif key == "work":
            search_filter["work"] = value
        else:
            raise ValueError(f"bad --filter key {key!r}, expected work|volume")
    return search_filter


def show_hits(hits: list[dict]) -> None:
    if not hits:
        print("(no hits)")
        return
    for rank, hit in enumerate(hits, 1):
        print(f"[{rank}] score={hit['score']:.4f} {hit['chunk_id']}")
        print(f"    vol{hit['volume']:02d} | {hit['work']} | {hit['chapter']}")
        snippet = hit["text"][:400].replace("\n", " ")
        print(f"    {snippet}{'...' if len(hit['text']) > 400 else ''}")


def repl(top_k: int, search_filter: dict, collection: str) -> int:
    print(f"collection '{collection}' | top_k={top_k} | filter={search_filter or '{}'}")
    print("Ask in Russian or English (empty = again, quit/exit = leave).")
    while True:
        try:
            query = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not query:
            continue
        if query.lower() in ("quit", "exit"):
            return 0
        vector = embed.embed_query(query)
        hits = chroma.query_store(
            vector,
            top_k=top_k,
            search_filter=search_filter or None,
            collection_name=collection,
        )
        show_hits(hits)


def main(argv: list[str] | None = None) -> int:
    settings = load_settings()
    parser = argparse.ArgumentParser(description="Interactive search over tolstoy-ru.")
    parser.add_argument("--top-k", type=int, default=settings.top_k)
    parser.add_argument(
        "--filter", action="append", default=[], help="key=value, repeatable (work, volume)"
    )
    parser.add_argument("--collection", default=settings.collection)
    args = parser.parse_args(argv)
    try:
        search_filter = parse_filters(args.filter)
    except ValueError as exc:
        print(f"error: {exc}")
        return 1
    top_k = max(1, min(args.top_k, 20))
    return repl(top_k, search_filter, args.collection)


if __name__ == "__main__":
    raise SystemExit(main())
