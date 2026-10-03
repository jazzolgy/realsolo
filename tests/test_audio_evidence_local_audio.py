from __future__ import annotations

from pathlib import Path

from music_intelligence.audio_evidence.adapters.local_audio import (
    FFmpegSegmentMaterializer,
)
from music_intelligence.audio_evidence.adapters.source import AudioSource


def test_ffmpeg_segment_materializer_projects_playlist_range_to_local_source(tmp_path: Path):
    source_file = tmp_path / "playlist.mp3"
    source_file.write_bytes(b"audio")
    output_root = tmp_path / "segments"

    captured = {}

    def fake_runner(command):
        captured["command"] = tuple(command)
        output_root.mkdir(parents=True, exist_ok=True)
        (output_root / "BE-003.wav").write_bytes(b"segment")

    materializer = FFmpegSegmentMaterializer(
        output_root=str(output_root),
        runner=fake_runner,
    )
    result = materializer.materialize(
        AudioSource(
            source_id="BE-003",
            uri=str(source_file),
            start_seconds=708.0,
            end_seconds=1069.0,
            metadata={"title": "Autumn Leaves"},
        )
    )

    assert result.source_id == "BE-003:segment"
    assert result.start_seconds is None
    assert result.end_seconds is None
    assert result.metadata["source_time_offset_seconds"] == "708.000000"
    assert result.metadata["source_segment_duration_seconds"] == "361.000000"
    assert "-ss" in captured["command"]
    assert "-t" in captured["command"]


def test_ffmpeg_segment_materializer_is_noop_without_range(tmp_path: Path):
    source_file = tmp_path / "single.wav"
    source_file.write_bytes(b"audio")
    source = AudioSource(source_id="single", uri=str(source_file))

    result = FFmpegSegmentMaterializer(
        output_root=str(tmp_path / "segments"),
        runner=lambda command: (_ for _ in ()).throw(AssertionError("runner should not be called")),
    ).materialize(source)

    assert result is source
