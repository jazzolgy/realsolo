"""Evidence-aware bebop style profile.

The profile stores *provisional priors*, not universal truths.  Values are
engineering defaults constrained by uploaded method-book study and the Parker
compilation survey.  They must later be calibrated by timestamped expert
annotations and identified recordings.

Nothing here is a LegendProfile for a named drummer.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PriorEvidence(str, Enum):
    METHOD_SUPPORTED = "method_supported"
    AUDIO_SUPPORTED = "audio_supported"
    HISTORICALLY_SUPPORTED = "historically_supported"
    ENGINEERING_PROVISIONAL = "engineering_provisional"


@dataclass(frozen=True)
class BebopPrior:
    value: float
    evidence: frozenset[PriorEvidence]
    note: str = ""

    def validate(self) -> None:
        if not 0.0 <= self.value <= 1.0:
            raise ValueError("bebop prior value must be within 0..1")
        if not self.evidence:
            raise ValueError("bebop prior must carry evidence provenance")


@dataclass(frozen=True)
class BebopStyleProfile:
    """Style-level priors shared across early/straight-ahead bebop contexts."""

    ride_time_salience: BebopPrior
    skip_surface_flexibility: BebopPrior
    hihat_24_anchor: BebopPrior
    comp_selectivity: BebopPrior
    intentional_non_response: BebopPrior
    bass_floor_support: BebopPrior
    bass_interactive_accent: BebopPrior
    phrase_pacing_memory: BebopPrior
    form_punctuation_opportunity: BebopPrior
    density_following_strength: BebopPrior

    def validate(self) -> None:
        for value in self.__dict__.values():
            value.validate()


DEFAULT_BEBOP_PROFILE = BebopStyleProfile(
    ride_time_salience=BebopPrior(
        0.92,
        frozenset({
            PriorEvidence.METHOD_SUPPORTED,
            PriorEvidence.AUDIO_SUPPORTED,
            PriorEvidence.HISTORICALLY_SUPPORTED,
        }),
        "Ride-led time is strongly supported; the number is provisional.",
    ),
    skip_surface_flexibility=BebopPrior(
        0.72,
        frozenset({
            PriorEvidence.METHOD_SUPPORTED,
            PriorEvidence.AUDIO_SUPPORTED,
            PriorEvidence.ENGINEERING_PROVISIONAL,
        }),
        "Skip-beat language is important but should not become a fixed loop.",
    ),
    hihat_24_anchor=BebopPrior(
        0.78,
        frozenset({
            PriorEvidence.METHOD_SUPPORTED,
            PriorEvidence.AUDIO_SUPPORTED,
            PriorEvidence.ENGINEERING_PROVISIONAL,
        }),
        "2&4 is a strong anchor prior with contextual omission.",
    ),
    comp_selectivity=BebopPrior(
        0.80,
        frozenset({
            PriorEvidence.METHOD_SUPPORTED,
            PriorEvidence.AUDIO_SUPPORTED,
            PriorEvidence.ENGINEERING_PROVISIONAL,
        }),
        "Comping should be selective rather than subdivision-independent.",
    ),
    intentional_non_response=BebopPrior(
        0.66,
        frozenset({
            PriorEvidence.METHOD_SUPPORTED,
            PriorEvidence.AUDIO_SUPPORTED,
            PriorEvidence.ENGINEERING_PROVISIONAL,
        }),
        "Explicit silence/non-response is required; exact probability awaits annotation.",
    ),
    bass_floor_support=BebopPrior(
        0.52,
        frozenset({
            PriorEvidence.METHOD_SUPPORTED,
            PriorEvidence.HISTORICALLY_SUPPORTED,
            PriorEvidence.ENGINEERING_PROVISIONAL,
        }),
        "Quiet bass-drum floor support is separate from accents.",
    ),
    bass_interactive_accent=BebopPrior(
        0.48,
        frozenset({
            PriorEvidence.METHOD_SUPPORTED,
            PriorEvidence.HISTORICALLY_SUPPORTED,
            PriorEvidence.ENGINEERING_PROVISIONAL,
        }),
        "Bomb/accent probability is context-sensitive; value is only a candidate weight.",
    ),
    phrase_pacing_memory=BebopPrior(
        0.88,
        frozenset({
            PriorEvidence.METHOD_SUPPORTED,
            PriorEvidence.ENGINEERING_PROVISIONAL,
        }),
        "Phrase-scale pacing is strongly motivated by Riley's pacing/transposition work.",
    ),
    form_punctuation_opportunity=BebopPrior(
        0.70,
        frozenset({
            PriorEvidence.METHOD_SUPPORTED,
            PriorEvidence.AUDIO_SUPPORTED,
            PriorEvidence.ENGINEERING_PROVISIONAL,
        }),
        "Form boundaries create opportunities, not mandatory fills.",
    ),
    density_following_strength=BebopPrior(
        0.25,
        frozenset({
            PriorEvidence.METHOD_SUPPORTED,
            PriorEvidence.ENGINEERING_PROVISIONAL,
        }),
        "Low by design: drummer density must not mechanically track soloist density.",
    ),
)

DEFAULT_BEBOP_PROFILE.validate()
