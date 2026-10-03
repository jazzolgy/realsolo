"""Source-separation aware orchestration for Audio Evidence Engine."""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Callable, Sequence

from .adapters.source import AudioSource
from .context.models import ContextEvidence
from .detectors.base import AudioObservationDetector
from .detectors.separation import SourceSeparator
from .observation.models import AudioObservation
from .posterior.fusion import (
    BoundedContextPosterior,
    ContextualAudioHypothesis,
)

ContextProvider = Callable[[AudioObservation], Sequence[ContextEvidence]]


@dataclass
class SeparatedAudioEvidencePipeline:
    """Run one observation detector across source-separation outputs."""

    detector: AudioObservationDetector
    separator: SourceSeparator | None = None
    context_provider: ContextProvider | None = None
    posterior: BoundedContextPosterior = field(
        default_factory=BoundedContextPosterior
    )

    def analyze(
        self,
        source: AudioSource,
    ) -> tuple[ContextualAudioHypothesis, ...]:
        source.validate()
        results: list[ContextualAudioHypothesis] = []

        if self.separator is None:
            observations = tuple(self.detector.detect(source))
            for observation in observations:
                observation.validate()
                factors = (
                    tuple(self.context_provider(observation))
                    if self.context_provider is not None
                    else ()
                )
                results.append(
                    self.posterior.revise_instrument(observation, factors)
                )
            return tuple(results)

        separated_items = tuple(self.separator.separate(source))
        for separated in separated_items:
            separated.validate()
            observations = tuple(self.detector.detect(separated.source))
            for observation in observations:
                observation.validate()
                enriched = replace(
                    observation,
                    separation=separated.metadata,
                    provenance=observation.provenance
                    + ("audio-evidence:source-separation",),
                )
                factors = (
                    tuple(self.context_provider(enriched))
                    if self.context_provider is not None
                    else ()
                )
                results.append(
                    self.posterior.revise_instrument(enriched, factors)
                )

        return tuple(results)
