from __future__ import annotations

from pathlib import Path

import pytest

from music_intelligence.audio_evidence.adapters.source import AudioSource
from music_intelligence.audio_evidence.detectors.demucs_adapter import (
    DemucsCLISeparator,
)


def test_demucs_adapter_builds_source_neutral_stem_outputs(tmp_path: Path):
    source_file = tmp_path / "mix.wav"
    source_file.write_bytes(b"not-real-audio")
    output_root = tmp_path / "separated"

    captured = {}

    def fake_runner(command):
        captured["command"] = tuple(command)
        stem_dir = output_root / "htdemucs" / source_file.stem
        stem_dir.mkdir(parents=True)
        for name in ("drums", "bass", "other", "vocals"):
            (stem_dir / f"{name}.wav").write_bytes(b"stem")

    separator = DemucsCLISeparator(
        output_root=str(output_root),
        runner=fake_runner,
    )
    results = separator.separate(
        AudioSource(
            source_id="mix-001",
            uri=str(source_file),
            start_seconds=5.0,
            end_seconds=10.0,
            metadata={"rights": "DERIVED_ONLY"},
        )
    )

    assert len(results) == 4
    assert {item.metadata.stem_label for item in results} == {
        "drums",
        "bass",
        "other",
        "vocals",
    }
    assert all(item.source.start_seconds is None for item in results)
    assert all(item.source.end_seconds is None for item in results)
    assert all(item.source.metadata["parent_source_id"] == "mix-001" for item in results)
    assert "-m" in captured["command"]
    assert "demucs.separate" in captured["command"]


def test_demucs_adapter_does_not_require_demucs_at_import_time(tmp_path: Path):
    source_file = tmp_path / "mix.wav"
    source_file.write_bytes(b"x")

    called = {"value": False}

    def fake_runner(command):
        called["value"] = True
        stem_dir = tmp_path / "out" / "htdemucs" / source_file.stem
        stem_dir.mkdir(parents=True)
        (stem_dir / "bass.wav").write_bytes(b"stem")

    separator = DemucsCLISeparator(
        output_root=str(tmp_path / "out"),
        expected_stems=("bass",),
        runner=fake_runner,
    )
    results = separator.separate(
        AudioSource(source_id="mix", uri=str(source_file))
    )

    assert called["value"] is True
    assert results[0].source.metadata["stem_label"] == "bass"


def test_demucs_adapter_rejects_unmaterialized_time_range(tmp_path: Path):
    source_file = tmp_path / "playlist.mp3"
    source_file.write_bytes(b"x")
    separator = DemucsCLISeparator(
        output_root=str(tmp_path / "out"),
        runner=lambda command: None,
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


def test_demucs_6s_profile_includes_pretrained_piano_and_guitar_stems(tmp_path: Path):
    source_file = tmp_path / "mix.wav"
    source_file.write_bytes(b"x")
    output_root = tmp_path / "out"

    def fake_runner(command):
        stem_dir = output_root / "htdemucs_6s" / source_file.stem
        stem_dir.mkdir(parents=True)
        for name in ("drums", "bass", "other", "vocals", "guitar", "piano"):
            (stem_dir / f"{name}.wav").write_bytes(b"stem")

    separator = DemucsCLISeparator(
        output_root=str(output_root),
        model_name="htdemucs_6s",
        runner=fake_runner,
    )
    results = separator.separate(
        AudioSource(source_id="mix", uri=str(source_file))
    )

    assert {item.metadata.stem_label for item in results} == {
        "drums",
        "bass",
        "other",
        "vocals",
        "guitar",
        "piano",
    }


def test_demucs_adapter_supports_local_six_stem_checkpoint_repository(tmp_path: Path):
    source_file = tmp_path / "mix.wav"
    source_file.write_bytes(b"x")
    model_repo = tmp_path / "models"
    model_repo.mkdir()
    (model_repo / "5c90dfd2-34c22ccb.th").write_bytes(b"checkpoint")
    output_root = tmp_path / "out"

    captured = {}

    def fake_runner(command):
        captured["command"] = tuple(command)
        stem_dir = output_root / "5c90dfd2" / source_file.stem
        stem_dir.mkdir(parents=True)
        for name in ("drums", "bass", "other", "vocals", "guitar", "piano"):
            (stem_dir / f"{name}.wav").write_bytes(b"stem")

    separator = DemucsCLISeparator(
        output_root=str(output_root),
        model_name="htdemucs_6s",
        model_repository=str(model_repo),
        model_signature="5c90dfd2",
        runner=fake_runner,
    )
    results = separator.separate(
        AudioSource(source_id="mix", uri=str(source_file))
    )

    assert "--repo" in captured["command"]
    assert str(model_repo) in captured["command"]
    assert "5c90dfd2" in captured["command"]
    assert {item.metadata.stem_label for item in results} == {
        "drums",
        "bass",
        "other",
        "vocals",
        "guitar",
        "piano",
    }
    assert all(
        item.source.metadata["separator_model_repository"] == str(model_repo)
        for item in results
    )


def test_demucs_local_repository_requires_signature(tmp_path: Path):
    model_repo = tmp_path / "models"
    model_repo.mkdir()

    with pytest.raises(ValueError, match="model_signature"):
        DemucsCLISeparator(
            output_root=str(tmp_path / "out"),
            model_repository=str(model_repo),
        )
