#!/usr/bin/env python3
"""Refresh the public example from its source Topic Workspace."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


EXCLUDED_PARTS = {".mypy_cache", ".ruff_cache", "__pycache__"}
ROOT_FILES = (
    "isomer-topic-workspace-summary.md",
    "pixi.lock",
    "topic-workspace.toml",
)


def _excluded(relative_path: Path) -> bool:
    return (
        bool(EXCLUDED_PARTS.intersection(relative_path.parts))
        or relative_path.name == "index.sqlite"
        or relative_path.suffix == ".pyc"
    )


def _replace_tree(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    for source_path in source.rglob("*"):
        relative_path = source_path.relative_to(source)
        if _excluded(relative_path) or source_path.is_symlink():
            continue
        destination_path = destination / relative_path
        if source_path.is_dir():
            destination_path.mkdir(parents=True, exist_ok=True)
        elif source_path.is_file():
            destination_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, destination_path)


def _sanitizable_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        try:
            path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        files.append(path)
    return files


def _sanitize_text_files(files: list[Path], replacements: list[tuple[str, str]]) -> None:
    for path in files:
        text = path.read_text(encoding="utf-8")
        updated = text
        for original, replacement in replacements:
            if original:
                updated = updated.replace(original, replacement)
        if updated != text:
            path.write_text(updated, encoding="utf-8")


def _digest_json(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _refresh_payload_digests(records_root: Path) -> int:
    digest_replacements: dict[str, str] = {}
    manifests: list[tuple[Path, dict[str, object]]] = []
    for manifest_path in records_root.rglob("manifest.json"):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        payload_file = manifest.get("payload_file")
        old_digest = manifest.get("payload_digest")
        if not isinstance(payload_file, str) or not isinstance(old_digest, str):
            continue
        payload_path = manifest_path.parent / payload_file
        if not payload_path.is_file():
            continue
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
        new_digest = _digest_json(payload)
        manifest["payload_digest"] = new_digest
        previous = digest_replacements.setdefault(old_digest, new_digest)
        if previous != new_digest:
            raise ValueError(f"digest collision after sanitization: {old_digest}")
        manifests.append((manifest_path, manifest))

    for markdown_path in records_root.rglob("*.md"):
        text = markdown_path.read_text(encoding="utf-8")
        updated = text
        for old_digest, new_digest in digest_replacements.items():
            updated = updated.replace(old_digest, new_digest)
        if updated != text:
            markdown_path.write_text(updated, encoding="utf-8")

    for manifest_path, manifest in manifests:
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return len(manifests)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_workspace", type=Path)
    parser.add_argument("--source-project-root", type=Path)
    parser.add_argument("--ncu-path", type=Path)
    parser.add_argument("--source-home", type=Path)
    args = parser.parse_args()

    source_workspace = args.source_workspace.resolve()
    project_root = (args.source_project_root or source_workspace.parents[2]).resolve()
    ncu_path = (args.ncu_path or Path.home() / ".pixi/bin/ncu").resolve()
    source_home = (args.source_home or ncu_path.parents[2]).resolve()
    destination_root = Path(__file__).resolve().parents[1]

    for directory in ("intent", "records"):
        _replace_tree(source_workspace / directory, destination_root / directory)
    _replace_tree(source_workspace / "repos/topic-main/src", destination_root / "repos/topic-main/src")
    _replace_tree(
        project_root / "skillset/toolboxes/gpu-analytical-modeling",
        destination_root / "skillset/toolboxes/gpu-analytical-modeling",
    )
    for filename in ROOT_FILES:
        shutil.copy2(source_workspace / filename, destination_root / filename)
    shutil.copy2(
        source_workspace / "repos/topic-main/host-b200-spec.md",
        destination_root / "repos/topic-main/host-b200-spec.md",
    )

    replacements = [
        (str(ncu_path), "<NCU_PATH>"),
        (str(project_root), "<PROJECT_ROOT>"),
        (str(source_home), "<USER_HOME>"),
    ]
    refreshed_roots = [
        destination_root / "intent",
        destination_root / "records",
        destination_root / "repos/topic-main/src",
        destination_root / "repos/topic-main/host-b200-spec.md",
        destination_root / "skillset/toolboxes/gpu-analytical-modeling",
        *(destination_root / filename for filename in ROOT_FILES),
    ]
    text_files: list[Path] = []
    for root in refreshed_roots:
        text_files.extend([root] if root.is_file() else _sanitizable_files(root))
    _sanitize_text_files(text_files, replacements)
    manifest_count = _refresh_payload_digests(destination_root / "records")

    leaked = [
        path
        for path in text_files
        if any(original and original in path.read_text(encoding="utf-8") for original, _ in replacements)
    ]
    if leaked:
        raise RuntimeError("sanitization check failed: " + ", ".join(str(path) for path in leaked))
    print(f"Refreshed sanitized export; updated {manifest_count} structured-record manifests.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
