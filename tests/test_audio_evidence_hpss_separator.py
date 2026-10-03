from __future__ import annotations

from pathlib import Path

import pytest

from music_intelligence.audio_evidence.adapters.source import AudioSource
from music_intelligence.audio_evidence.detectors.hpss_separator import (
    LibrosaHPSSSeparator,
)


def test_hpss_separator_is_optional_at_import_time(tmp_path: Path):
    separator = LibrosaHPSSSeparator(output_root=str(tmp_path / "stems"))
    assert separator.separator_id == "librosa:hpss:v0.1"


def test_hpss_separator_rejects_unmaterialized_range_before_optional_dependency_use(
    tmp_path: Path,
):
    source_file = tmp_path / "playlist.mp3"
    source_file.write_bytes(b"x")
    separator = LibrosaHPSSSeparator(output_root=str(tmp_path / "stems"))

    with pytest.raises(ValueError, match="materialized source segment"):
        separator.separate(
            AudioSource(
                source_id="BE-003",
                uri=str(source_file),
                start_seconds=708.0,
                end_seconds=1069.0,
            )
        )
