from __future__ import annotations

from pathlib import Path

import pytest

from music_intelligence.audio_evidence.adapters.source import AudioSource
from music_intelligence.audio_evidence.detectors.librosa_baseline import (
    LibrosaOnsetDetector,
    LibrosaPercussiveTokenDetector,
    LibrosaSourceLoader,
    LibrosaSpectralPeakPitchDetector,
    LibrosaTimbreDetector,
)


def test_librosa_baseline_module_is_optional_at_import_time():
    loader = LibrosaSourceLoader(sample_rate=22050)
    assert loader.sample_rate == 22050

    assert LibrosaOnsetDetector(loader=loader).detector_id.startswith("librosa:")
    assert LibrosaSpectralPeakPitchDetector(loader=loader).detector_id.startswith("librosa:")
    assert LibrosaTimbreDetector(loader=loader).detector_id.startswith("librosa:")
    assert LibrosaPercussiveTokenDetector(loader=loader).detector_id.startswith("librosa:")


def test_librosa_source_loader_rejects_missing_uri_before_optional_dependency_load():
    loader = LibrosaSourceLoader()

    with pytest.raises(ValueError, match="AudioSource.uri"):
        loader.load(AudioSource(source_id="no-uri"))


def test_librosa_source_loader_rejects_missing_file_before_optional_dependency_load(tmp_path: Path):
    loader = LibrosaSourceLoader()
    missing = tmp_path / "missing.mp3"

    with pytest.raises(FileNotFoundError):
        loader.load(AudioSource(source_id="missing", uri=str(missing)))


def test_librosa_pitch_detector_declares_polyphonic_hypothesis_limit():
    detector = LibrosaSpectralPeakPitchDetector(max_pitches_per_onset=6)
    assert detector.max_pitches_per_onset == 6
    assert detector.relative_peak_threshold == pytest.approx(0.18)
