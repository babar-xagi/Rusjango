"""Shared Docker/test templates and file ownership for reversible scaffolding."""

from __future__ import annotations

from importlib.resources import files
import json
from pathlib import Path

from rusjango.config import load_rusjango_config

MANIFEST = ".rusjango-features.json"
PROFILES = {
    "docker": [
        "Dockerfile",
        "compose.yml",
        ".dockerignore",
        "settings_docker.py",
        "docker_app.py",
    ],
    "tests": ["tests/conftest.py", "tests/test_health.py"],
    "admin": ["admin.py"],
}


def _safe_path(root: Path, name: str) -> Path:
    path = root / name
    if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(
            f"Refusing to edit a symlink or path outside the project: {name}"
        )
    # Also reject symlinked directories even when they point back inside the project.
    for parent in path.parents:
        if parent == root:
            break
        if parent.is_symlink():
            raise ValueError(f"Refusing to edit a symlinked directory: {name}")
    return path


def _load_manifest(root: Path) -> dict:
    path = _safe_path(root, MANIFEST)
    if not path.exists():
        return {"format": 1, "features": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise ValueError("Invalid .rusjango-features.json") from exc
    if (
        not isinstance(data, dict)
        or type(data.get("format")) is not int
        or data.get("format") != 1
        or not isinstance(data.get("features"), dict)
    ):
        raise ValueError("Invalid .rusjango-features.json format")
    for feature, entries in data["features"].items():
        if (
            feature not in PROFILES
            or not isinstance(entries, dict)
            or set(entries) != set(PROFILES[feature])
        ):
            raise ValueError("Invalid scaffold ownership entries")
        if not all(isinstance(content, str) for content in entries.values()):
            raise ValueError("Invalid scaffold ownership content")
    return data


def _save_manifest(root: Path, data: dict) -> None:
    path = _safe_path(root, MANIFEST)
    if data["features"]:
        path.write_bytes(
            (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode()
        )
    elif path.exists():
        path.unlink()


def add_feature(root: Path, feature: str) -> bool:
    data = _load_manifest(root)
    if feature in data["features"]:
        return False
    paths = {name: _safe_path(root, name) for name in PROFILES[feature]}
    if feature == "docker":
        for alias in ("compose.yaml", "docker-compose.yml", "docker-compose.yaml"):
            if (root / alias).exists():
                raise ValueError(f"Existing Docker configuration preserved: {alias}")
    for name, path in paths.items():
        if path.exists():
            raise ValueError(f"Existing file preserved: {name}")
    config = load_rusjango_config(root)
    substitutions = {
        "settings_path": config.get("settings", "settings.py"),
        "app_path": config.get("app", "main:app"),
    }
    if not all(isinstance(value, str) for value in substitutions.values()):
        raise ValueError("Project settings/app paths must be strings")
    module, separator, attribute = substitutions["app_path"].partition(":")
    if not separator or not module or not attribute:
        raise ValueError("Project app must use module:attribute syntax")
    if not (root / substitutions["settings_path"]).is_file():
        raise ValueError("Project settings file does not exist")
    contents = {}
    for name in paths:
        filename = name.removeprefix("tests/")
        if filename == ".dockerignore":
            filename = "dockerignore"
        content = (
            files("rusjango")
            .joinpath("templates", feature, filename + ".tpl")
            .read_text(encoding="utf-8")
        )
        for key, value in substitutions.items():
            content = content.replace(
                "{{ " + key + " }}", json.dumps(value, ensure_ascii=False)
            )
        contents[name] = content
    # Preflight every file before changing the project.
    for name, path in paths.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(contents[name].encode())
    data["features"][feature] = contents
    _save_manifest(root, data)
    return True


def remove_feature(root: Path, feature: str) -> list[str]:
    data = _load_manifest(root)
    entries = data["features"].get(feature)
    if entries is None:
        raise ValueError(f"No tracked {feature} scaffold found")
    paths = {name: _safe_path(root, name) for name in entries}
    kept = []
    for name, path in paths.items():
        if path.exists():
            if path.is_file() and path.read_bytes() == entries[name].encode():
                path.unlink()
            else:
                kept.append(name)
    del data["features"][feature]
    _save_manifest(root, data)
    if feature == "tests":
        directory = root / "tests"
        if directory.is_dir() and not any(directory.iterdir()):
            directory.rmdir()
    return kept
