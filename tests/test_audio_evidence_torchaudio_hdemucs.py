from __future__ import annotations

from pathlib import Path

import pytest

from music_intelligence.audio_evidence.adapters.source import AudioSource
from music_intelligence.audio_evidence.detectors.torchaudio_hdemucs import (
    TorchAudioHDemucsSeparator,
)


def test_torchaudio_hdemucs_adapter_is_optional_at_import_time(tmp_path: Path):
    separator = TorchAudioHDemucsSeparator(
        output_root=str(tmp_path / "stems")
    )
    assert separator.bundle_name == "HDEMUCS_HIGH_MUSDB_PLUS"
    assert separator.separator_id == "torchaudio-hdemucs:v0.1"


def test_torchaudio_hdemucs_rejects_unknown_bundle(tmp_path: Path):
    with pytest.raises(ValueError, match="unsupported"):
        TorchAudioHDemucsSeparator(
            output_root=str(tmp_path / "stems"),
            bundle_name="UNKNOWN",
        )


def test_torchaudio_hdemucs_rejects_unmaterialized_time_range(tmp_path: Path):
    source_file = tmp_path / "playlist.mp3"
    source_file.write_bytes(b"x")
    separator = TorchAudioHDemucsSeparator(
        output_root=str(tmp_path / "stems")
    )

    with pytest.raises(ValueError, match="materialized source segment"):
        separator.separate(
            AudioSource(
                source_id="BE-003",
                uri=str(source_file),
                start_seconds=708.0,
                end_seconds=1069.0,
            )
        )
