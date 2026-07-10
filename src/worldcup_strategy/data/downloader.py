"""Idempotent StatsBomb Open Data acquisition."""

import subprocess
from pathlib import Path

from worldcup_strategy.data.manifests import build_source_manifest, write_json


def fetch_repository(source_url: str, destination: Path, manifest_path: Path) -> dict[str, object]:
    """Clone a shallow source checkout, or reuse an existing valid checkout."""
    if destination.exists():
        if not (destination / ".git").is_dir() or not (destination / "data").is_dir():
            raise RuntimeError(f"Destination exists but is not a StatsBomb checkout: {destination}")
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "clone", "--depth", "1", source_url, str(destination)],
            check=True,
        )
    manifest = build_source_manifest(destination, source_url)
    write_json(manifest_path, manifest)
    return manifest
