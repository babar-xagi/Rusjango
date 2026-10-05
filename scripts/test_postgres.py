"""Run the suite against a disposable PostgreSQL server (Python 3.12 runner)."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile

import pgserver


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    python = str(Path(sys.argv[1]).absolute()) if len(sys.argv) > 1 else sys.executable
    with tempfile.TemporaryDirectory(prefix="rusjango-postgres-") as directory:
        server = pgserver.get_server(Path(directory), cleanup_mode="stop")
        try:
            env = {
                **os.environ,
                "PYTHONPATH": str(root / "python/rusjango/src"),
                "RUSJANGO_TEST_POSTGRES_DSN": server.get_uri(),
            }
            return subprocess.run(
                [python, "-m", "pytest", str(root / "python/rusjango/tests"), "-q"],
                cwd=root,
                env=env,
            ).returncode
        finally:
            server.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
