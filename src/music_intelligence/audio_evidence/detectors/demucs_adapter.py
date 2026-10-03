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
    expected_stems: tuple[str, ...] | None = None
    model_repository: str | None = None
    model_signature: str | None = None
    runner: CommandRunner = _default_runner
    separator_id: str = "demucs-cli:v0.3"

    def __post_init__(self) -> None:
        six_stem_model = self.model_name == "htdemucs_6s" or self.model_signature == "5c90dfd2"
        if self.expected_stems is None:
            self.expected_stems = (
                ("drums", "bass", "other", "vocals", "guitar", "piano")
                if six_stem_model
                else ("drums", "bass", "other", "vocals")
            )
        if self.model_repository is not None:
            repository = Path(self.model_repository)
            if not repository.is_dir():
                raise FileNotFoundError(repository)
            if not self.model_signature:
                raise ValueError(
                    "model_signature is required when model_repository is provided"
                )

    def separate(self, source: AudioSource) -> Sequence[SeparatedSource]:
        source.validate()
        if not source.uri:
            raise ValueError("Demucs separator requires AudioSource.uri")
        if source.start_seconds is not None or source.end_seconds is not None:
            raise ValueError(
                "Demucs separator requires a materialized source segment; "
                "use FFmpegSegmentMaterializer before separation"
            )

        input_path = Path(source.uri)
        if not input_path.exists():
            raise FileNotFoundError(input_path)

        output_root = Path(self.output_root)
        output_root.mkdir(parents=True, exist_ok=True)

        selected_model = self.model_signature or self.model_name
        command = [
            sys.executable,
            "-m",
            "demucs.separate",
        ]
        if self.model_repository is not None:
            command.extend(["--repo", self.model_repository])
        command.extend(
            [
                "-n",
                selected_model,
                "-o",
                str(output_root),
                str(input_path),
            ]
        )
        self.runner(tuple(command))

        stem_dir = output_root / selected_model / input_path.stem
        separated: list[SeparatedSource] = []
        for stem_label in self.expected_stems or ():
            stem_path = stem_dir / f"{stem_label}.wav"
            if not stem_path.exists():
                continue
            metadata = dict(source.metadata)
            metadata.update(
                {
                    "stem_label": stem_label,
                    "separator_id": self.separator_id,
                    "separator_model": selected_model,
                    "separator_named_profile": self.model_name,
                    "separator_model_repository": self.model_repository or "remote-default",
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
                        model_id=f"demucs:{selected_model}",
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
