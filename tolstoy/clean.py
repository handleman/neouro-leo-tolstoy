"""Thin CLI: python -m tolstoy.clean --volume N | --all."""

from tolstoy.ingest.clean import main

if __name__ == "__main__":
    raise SystemExit(main())
