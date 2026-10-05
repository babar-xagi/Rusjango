"""Check package/native versions and an optional release tag before publishing."""

from __future__ import annotations

import ast
from pathlib import Path
import sys
import tomllib


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    package = tomllib.loads((root / "python/rusjango/pyproject.toml").read_text())
    workspace = tomllib.loads((root / "Cargo.toml").read_text())
    module = ast.parse((root / "python/rusjango/src/rusjango/__init__.py").read_text())
    fallback = next(
        ast.literal_eval(node.value)
        for node in module.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "__version__"
            for target in node.targets
        )
    )
    version = package["project"]["version"]
    if not version == workspace["workspace"]["package"]["version"] == fallback:
        raise SystemExit(
            "Python package, Rust workspace, and fallback versions must match"
        )
    if len(sys.argv) > 1:
        tag = sys.argv[1]
        if tag != f"v{version}":
            raise SystemExit(
                f"Release tag {tag!r} does not match package version {version}"
            )
        if not (root / "docs/releases" / f"{version}.md").is_file():
            raise SystemExit(f"Missing release notes for {version}")
    print(f"Release versions match: {version}")


if __name__ == "__main__":
    main()
