"""Reproducible pretrained-separation validation helpers.

This module stays inside Audio Evidence. It compares acoustic evidence before and
after separation without importing Core, Transcription, Learning, or notation.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

from ..adapters.local_audio import FFmpegSegmentMaterializer
from ..adapters.source import AudioSource
from ..calibration.ambiguity import AmbiguitySummary, summarize_instrument_ambiguity
from ..detectors.base import AudioObservationDetector
from ..detectors.demucs_adapter import DemucsCLISeparator
from ..posterior.fusion import BoundedContextPosterior, ContextualAudioHypothesis


@dataclass(frozen=True)
class StemValidationResult:
    stem_label: str
    hypotheses: tuple[ContextualAudioHypothesis, ...]
    ambiguity: AmbiguitySummary


@dataclass(frozen=True)
class PretrainedSeparationValidation:
    source_id: str
    model_id: str
    mixture_ambiguity: AmbiguitySummary
    stems: tuple[StemValidationResult, ...]


def validate_pretrained_separation(
    *,
    source: AudioSource,
    detector_factory: Callable[[], AudioObservationDetector],
    segment_output_root: str,
    separation_output_root: str,
    model_repository: str,
    model_signature: str = "5c90dfd2",
    model_name: str = "htdemucs_6s",
) -> PretrainedSeparationValidation:
    """Run one source through mixture and local-checkpoint separation paths.

    The function requires an explicit local model repository. It never downloads
    model weights and therefore keeps checkpoint acquisition outside engine
    inference and provenance.
    """

    repository = Path(model_repository)
    if not repository.is_dir():
        raise FileNotFoundError(repository)

    materialized = FFmpegSegmentMaterializer(
        output_root=segment_output_root,
    ).materialize(source)

    posterior = BoundedContextPosterior()
    mixture_detector = detector_factory()
    mixture = tuple(
        posterior.revise_instrument(observation)
        for observation in mixture_detector.detect(materialized)
    )
    mixture_ambiguity = summarize_instrument_ambiguity(mixture)

    separator = DemucsCLISeparator(
        output_root=separation_output_root,
        model_name=model_name,
        model_repository=str(repository),
        model_signature=model_signature,
    )
    separated = tuple(separator.separate(materialized))

    stems: list[StemValidationResult] = []
    for item in separated:
        detector = detector_factory()
        hypotheses = tuple(
            posterior.revise_instrument(observation)
            for observation in detector.detect(item.source)
        )
        stems.append(
            StemValidationResult(
                stem_label=item.metadata.stem_label or "unknown",
                hypotheses=hypotheses,
                ambiguity=summarize_instrument_ambiguity(hypotheses),
            )
        )

    return PretrainedSeparationValidation(
        source_id=source.source_id,
        model_id="demucs:" + model_signature,
        mixture_ambiguity=mixture_ambiguity,
        stems=tuple(stems),
    )
