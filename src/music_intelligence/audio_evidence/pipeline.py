"""Model-independent Audio Evidence Engine orchestration."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Sequence

from .adapters.source import AudioSource
from .context.models import ContextEvidence
from .detectors.base import AudioObservationDetector
from .observation.models import AudioObservation
from .posterior.fusion import (
    BoundedContextPosterior,
    ContextualAudioHypothesis,
)

ContextProvider = Callable[[AudioObservation], Sequence[ContextEvidence]]


@dataclass
class AudioEvidencePipeline:
    detector: AudioObservationDetector
    context_provider: ContextProvider | None = None
    posterior: BoundedContextPosterior = field(default_factory=BoundedContextPosterior)

    def analyze(
        self,
        source: AudioSource,
    ) -> tuple[ContextualAudioHypothesis, ...]:
        source.validate()
        observations = tuple(self.detector.detect(source))
        results: list[ContextualAudioHypothesis] = []
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
