"""CLI entry: rusjango dev (Python fallback)."""

from __future__ import annotations

import sys


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        from rusjango.server import main as dev_main

        dev_main(sys.argv[2:])
        return
    print("Usage: rusjango dev [--host HOST] [--port PORT] [--no-reload]", file=sys.stderr)
    raise SystemExit(1)


if __name__ == "__main__":
    main()
