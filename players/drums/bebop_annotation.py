"""Schema for timestamped expert bebop-drum annotations.

The schema intentionally records uncertainty.  Mix-level audio often cannot
reliably distinguish bass drum from acoustic bass or hi-hat from upper-band
recording artifacts, so instrument labels can remain UNKNOWN/uncertain until
expert or separated-stem verification.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .bebop import BassDrumIntent, BebopCompIntent, BebopInteractionState, BebopTimeIntent


class EvidenceConfidence(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DrumEventKind(str, Enum):
    RIDE = "ride"
    HIHAT = "hihat"
    SNARE = "snare"
    BASS_DRUM = "bass_drum"
    TOM = "tom"
    CRASH = "crash"
    SPACE = "space"
    UNKNOWN_PERCUSSIVE = "unknown_percussive"


@dataclass(frozen=True)
class BebopEventAnnotation:
    time_s: float
    event: DrumEventKind
    confidence: EvidenceConfidence
    accent_strength: float = 0.5
    phrase_phase: float | None = None
    notes: str = ""

    def validate(self) -> None:
        if self.time_s < 0:
            raise ValueError("time_s may not be negative")
        if not 0.0 <= self.accent_strength <= 1.0:
            raise ValueError("accent_strength must be within 0..1")
        if self.phrase_phase is not None and not 0.0 <= self.phrase_phase <= 1.0:
            raise ValueError("phrase_phase must be normalized to 0..1")


@dataclass(frozen=True)
class BebopPhraseAnnotation:
    source_audio: str
    start_s: float
    end_s: float
    periodicity_bpm: float | None
    periodicity_ambiguous: bool
    time_intent: BebopTimeIntent
    comp_intent: BebopCompIntent
    interaction_state: BebopInteractionState
    bass_drum_intent: BassDrumIntent | None = None
    soloist_density: float | None = None
    drummer_density: float | None = None
    phrase_boundary_confidence: float = 0.0
    verified_by_ear: bool = False
    events: tuple[BebopEventAnnotation, ...] = ()
    notes: str = ""

    def validate(self) -> None:
        if self.start_s < 0 or self.end_s <= self.start_s:
            raise ValueError("invalid phrase time span")
        if self.periodicity_bpm is not None and self.periodicity_bpm <= 0:
            raise ValueError("periodicity_bpm must be positive")
        for name in ("soloist_density", "drummer_density"):
            value = getattr(self, name)
            if value is not None and not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")
        if not 0.0 <= self.phrase_boundary_confidence <= 1.0:
            raise ValueError("phrase_boundary_confidence must be within 0..1")
        for event in self.events:
            event.validate()
            if not self.start_s <= event.time_s <= self.end_s:
                raise ValueError("event must fall inside phrase annotation")
