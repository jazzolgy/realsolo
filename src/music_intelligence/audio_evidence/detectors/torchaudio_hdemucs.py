"""Optional TorchAudio pretrained Hybrid Demucs separator.

This uses torchaudio pretrained HDEMUCS_HIGH_MUSDB(_PLUS) bundles. The bundle
is 4-stem (drums/bass/other/vocals), so piano remains inside the other stem.
It is a useful pretrained fallback when the six-stem checkpoint is unavailable.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from ..adapters.source import AudioSource
from ..observation.models import SeparationMetadata
from .separation import SeparatedSource


@dataclass
class TorchAudioHDemucsSeparator:
    output_root: str
    bundle_name: str = "HDEMUCS_HIGH_MUSDB_PLUS"
    device: str = "cpu"
    separator_id: str = "torchaudio-hdemucs:v0.1"

    def __post_init__(self) -> None:
        if self.bundle_name not in {
            "HDEMUCS_HIGH_MUSDB",
            "HDEMUCS_HIGH_MUSDB_PLUS",
        }:
            raise ValueError("unsupported torchaudio HDemucs bundle")

    def separate(self, source: AudioSource) -> Sequence[SeparatedSource]:
        source.validate()
        if not source.uri:
            raise ValueError("TorchAudio HDemucs requires AudioSource.uri")
        if source.start_seconds is not None or source.end_seconds is not None:
            raise ValueError(
                "TorchAudio HDemucs requires a materialized source segment"
            )
        path = Path(source.uri)
        if not path.exists():
            raise FileNotFoundError(path)

        try:
            import torch
            import torchaudio
        except ImportError as exc:
            raise RuntimeError(
                "TorchAudio HDemucs requires optional packages torch and torchaudio"
            ) from exc

        bundle = getattr(torchaudio.pipelines, self.bundle_name)
        model = bundle.get_model().to(self.device)
        waveform, sample_rate = torchaudio.load(str(path))
        if waveform.shape[0] == 1:
            waveform = waveform.repeat(2, 1)
        if sample_rate != bundle.sample_rate:
            waveform = torchaudio.functional.resample(
                waveform,
                sample_rate,
                bundle.sample_rate,
            )
        waveform = waveform.to(self.device)

        with torch.no_grad():
            estimates = model(waveform.unsqueeze(0))[0]

        sources = ("drums", "bass", "other", "vocals")
        output_root = Path(self.output_root)
        output_root.mkdir(parents=True, exist_ok=True)
        results: list[SeparatedSource] = []

        for index, stem_label in enumerate(sources):
            stem_path = output_root / f"{source.source_id}_{stem_label}.wav"
            torchaudio.save(
                str(stem_path),
                estimates[index].detach().cpu(),
                bundle.sample_rate,
            )
            metadata = dict(source.metadata)
            metadata.update(
                {
                    "stem_label": stem_label,
                    "separator_id": self.separator_id,
                    "separator_bundle": self.bundle_name,
                    "parent_source_id": source.source_id,
                    "piano_isolated": "false",
                }
            )
            results.append(
                SeparatedSource(
                    source=AudioSource(
                        source_id=f"{source.source_id}:stem:{stem_label}",
                        uri=str(stem_path),
                        metadata=metadata,
                    ),
                    metadata=SeparationMetadata(
                        model_id="torchaudio:" + self.bundle_name,
                        stem_label=stem_label,
                    ),
                )
            )
        return tuple(results)
