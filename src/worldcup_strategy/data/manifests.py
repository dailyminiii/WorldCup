"""Source provenance and checksums."""

import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str | None:
    """Return the SHA-256 digest, or null for an absent file."""
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_commit(repository: Path) -> str:
    """Read the checked-out source revision without mutating the repository."""
    result = subprocess.run(
        ["git", "-C", str(repository), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def write_json(path: Path, payload: Any) -> None:
    """Write stable, human-readable JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_source_manifest(repository: Path, source_url: str) -> dict[str, Any]:
    """Build source-level provenance."""
    return {
        "source": "StatsBomb Open Data",
        "source_url": source_url,
        "source_commit_sha": source_commit(repository),
        "download_timestamp_utc": datetime.now(UTC).isoformat(),
    }


def build_match_manifest(
    repository: Path, competition_id: int, season_id: int, match_id: int
) -> dict[str, Any]:
    """Build checksums and presence flags for one match's provider files."""
    event = repository / "data" / "events" / f"{match_id}.json"
    lineup = repository / "data" / "lineups" / f"{match_id}.json"
    three_sixty = repository / "data" / "three-sixty" / f"{match_id}.json"
    return {
        "source_commit_sha": source_commit(repository),
        "competition_id": competition_id,
        "season_id": season_id,
        "match_id": match_id,
        "events_file_present": event.is_file(),
        "lineup_file_present": lineup.is_file(),
        "three_sixty_file_present": three_sixty.is_file(),
        "events_sha256": sha256_file(event),
        "lineup_sha256": sha256_file(lineup),
        "three_sixty_sha256": sha256_file(three_sixty),
    }
