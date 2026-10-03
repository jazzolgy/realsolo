"""Optional librosa HPSS separator for offline validation.

HPSS is not an instrument separator. It provides harmonic/percussive evidence
streams so the source-separation boundary can be validated even when a learned
separator is unavailable.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from ..adapters.source import AudioSource
from ..observation.models import SeparationMetadata
from .librosa_baseline import LibrosaSourceLoader, _optional_modules
from .separation import SeparatedSource


@dataclass
class LibrosaHPSSSeparator:
    output_root: str
    loader: LibrosaSourceLoader | None = None
    separator_id: str = "librosa:hpss:v0.1"

    def separate(self, source: AudioSource) -> Sequence[SeparatedSource]:
        source.validate()
        if source.start_seconds is not None or source.end_seconds is not None:
            raise ValueError(
                "HPSS separator requires a materialized source segment"
            )

        loader = self.loader or LibrosaSourceLoader()
        decoded = loader.load(source)
        librosa, _ = _optional_modules()
        harmonic, percussive = librosa.effects.hpss(decoded.samples)

        try:
            import soundfile as sf
        except ImportError as exc:
            raise RuntimeError(
                "Librosa HPSS separator requires optional package 'soundfile'."
            ) from exc

        output_root = Path(self.output_root)
        output_root.mkdir(parents=True, exist_ok=True)

        results: list[SeparatedSource] = []
        for label, samples in (
            ("harmonic", harmonic),
            ("percussive", percussive),
        ):
            path = output_root / f"{source.source_id}_{label}.wav"
            sf.write(str(path), samples, decoded.sample_rate)
            metadata = dict(source.metadata)
            metadata.update(
                {
                    "stem_label": label,
                    "separator_id": self.separator_id,
                    "parent_source_id": source.source_id,
                }
            )
            results.append(
                SeparatedSource(
                    source=AudioSource(
                        source_id=f"{source.source_id}:stem:{label}",
                        uri=str(path),
                        metadata=metadata,
                    ),
                    metadata=SeparationMetadata(
                        model_id=self.separator_id,
                        stem_label=label,
                    ),
                )
            )

        return tuple(results)
