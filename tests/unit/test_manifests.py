from pathlib import Path
from typing import Any

import pytest

from worldcup_strategy.data.manifests import build_match_manifest


def test_match_manifest_preserves_absence_and_timestamp(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fixed_commit(repository: Path) -> str:
        return "abc123"

    monkeypatch.setattr("worldcup_strategy.data.manifests.source_commit", fixed_commit)
    manifest: dict[str, Any] = build_match_manifest(tmp_path, 43, 106, 1)
    assert manifest["source_commit_sha"] == "abc123"
    assert manifest["download_timestamp_utc"].endswith("+00:00")
    assert manifest["events_file_present"] is False
    assert manifest["events_sha256"] is None
