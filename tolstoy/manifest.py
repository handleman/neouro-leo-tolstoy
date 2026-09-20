"""Thin CLI: python -m tolstoy.manifest build|verify."""

from tolstoy.ingest.manifest import main

if __name__ == "__main__":
    raise SystemExit(main())
