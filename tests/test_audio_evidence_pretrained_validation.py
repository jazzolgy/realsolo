from __future__ import annotations

from pathlib import Path

import pytest

from music_intelligence.audio_evidence.adapters.source import AudioSource
from music_intelligence.audio_evidence.validation.pretrained import (
    validate_pretrained_separation,
)


def test_pretrained_validation_requires_explicit_local_checkpoint_repository(
    tmp_path: Path,
):
    source_file = tmp_path / "mix.wav"
    source_file.write_bytes(b"x")

    with pytest.raises(FileNotFoundError):
        validate_pretrained_separation(
            source=AudioSource(source_id="mix", uri=str(source_file)),
            detector_factory=lambda: None,
            segment_output_root=str(tmp_path / "segments"),
            separation_output_root=str(tmp_path / "stems"),
            model_repository=str(tmp_path / "missing-models"),
        )
