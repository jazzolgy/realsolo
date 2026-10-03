"""Optional Demucs CLI source-separation adapter.

The adapter owns only transport into/out of Demucs. It does not interpret stems
as musical meaning. Demucs is optional and invoked through an injectable runner
so the Audio Evidence package keeps no hard runtime dependency on it.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys
from typing import Callable, Sequence

from ..adapters.source import AudioSource
from ..observation.models import SeparationMetadata
from .separation import SeparatedSource

CommandRunner = Callable[[Sequence[str]], None]


def _default_runner(command: Sequence[str]) -> None:
    subprocess.run(tuple(command), check=True)


@dataclass
class DemucsCLISeparator:
    output_root: str
    model_name: str = "htdemucs"
    expected_stems: tuple[str, ...] = ("drums", "bass", "other", "vocals")
    runner: CommandRunner = _default_runner
    separator_id: str = "demucs-cli:v0.1"

    def separate(self, source: AudioSource) -> Sequence[SeparatedSource]:
        source.validate()
        if not source.uri:
            raise ValueError("Demucs separator requires AudioSource.uri")

        input_path = Path(source.uri)
        if not input_path.exists():
            raise FileNotFoundError(input_path)

        output_root = Path(self.output_root)
        output_root.mkdir(parents=True, exist_ok=True)

        command = (
            sys.executable,
            "-m",
            "demucs.separate",
            "-n",
            self.model_name,
            "-o",
            str(output_root),
            str(input_path),
        )
        self.runner(command)

        stem_dir = output_root / self.model_name / input_path.stem
        separated: list[SeparatedSource] = []
        for stem_label in self.expected_stems:
            stem_path = stem_dir / f"{stem_label}.wav"
            if not stem_path.exists():
                continue
            metadata = dict(source.metadata)
            metadata.update(
                {
                    "stem_label": stem_label,
                    "separator_id": self.separator_id,
                    "separator_model": self.model_name,
                    "parent_source_id": source.source_id,
                }
            )
            separated.append(
                SeparatedSource(
                    source=AudioSource(
                        source_id=f"{source.source_id}:stem:{stem_label}",
                        uri=str(stem_path),
                        start_seconds=None,
                        end_seconds=None,
                        metadata=metadata,
                    ),
                    metadata=SeparationMetadata(
                        model_id=f"demucs:{self.model_name}",
                        stem_label=stem_label,
                    ),
                )
            )

        if not separated:
            raise RuntimeError(
                "Demucs completed but no expected stem files were found under "
                + str(stem_dir)
            )
        return tuple(separated)
