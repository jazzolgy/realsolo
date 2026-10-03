"""Local-file source preparation for Audio Evidence Engine."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
from typing import Callable, Sequence

from .source import AudioSource

CommandRunner = Callable[[Sequence[str]], None]


def _default_runner(command: Sequence[str]) -> None:
    subprocess.run(tuple(command), check=True)


@dataclass
class FFmpegSegmentMaterializer:
    """Materialize an AudioSource time range into a standalone local file.

    This keeps model adapters such as Demucs unaware of playlist offsets.
    """

    output_root: str
    runner: CommandRunner = _default_runner
    audio_codec: str = "pcm_s16le"
    extension: str = ".wav"

    def materialize(self, source: AudioSource) -> AudioSource:
        source.validate()
        if not source.uri:
            raise ValueError("segment materializer requires AudioSource.uri")
        input_path = Path(source.uri)
        if not input_path.exists():
            raise FileNotFoundError(input_path)

        if source.start_seconds is None and source.end_seconds is None:
            return source

        start = float(source.start_seconds or 0.0)
        duration = None
        if source.end_seconds is not None:
            duration = float(source.end_seconds) - start
            if duration <= 0.0:
                raise ValueError("segment duration must be positive")

        output_root = Path(self.output_root)
        output_root.mkdir(parents=True, exist_ok=True)
        safe_id = "".join(
            character if character.isalnum() or character in "-_." else "_"
            for character in source.source_id
        )
        output_path = output_root / f"{safe_id}{self.extension}"

        command: list[str] = [
            "ffmpeg",
            "-y",
            "-ss",
            f"{start:.6f}",
            "-i",
            str(input_path),
        ]
        if duration is not None:
            command.extend(["-t", f"{duration:.6f}"])
        command.extend(
            [
                "-vn",
                "-acodec",
                self.audio_codec,
                str(output_path),
            ]
        )
        self.runner(tuple(command))

        if not output_path.exists():
            raise RuntimeError(
                "ffmpeg completed but segment file was not created: "
                + str(output_path)
            )

        metadata = dict(source.metadata)
        metadata.update(
            {
                "parent_source_id": source.source_id,
                "source_time_offset_seconds": f"{start:.6f}",
                "source_segment_materializer": "ffmpeg:v0.1",
            }
        )
        if duration is not None:
            metadata["source_segment_duration_seconds"] = f"{duration:.6f}"

        return AudioSource(
            source_id=source.source_id + ":segment",
            uri=str(output_path),
            start_seconds=None,
            end_seconds=None,
            metadata=metadata,
        )
