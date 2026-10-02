"""v1.30 scalable legend-style intelligence.

The Music Intelligence Core must not be bound to any single musician. This
module provides generic style/legend abstractions that can be populated from
Parker now and other master musicians later.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Mapping, Sequence


@dataclass(frozen=True)
class MusicalContextVector:
    harmony_function: str = "unknown"
    chord_symbol: str = ""
    metric_position: float = 0.0
    phrase_maturity: float = 0.0
    tension: float = 0.0
    register_norm: float = 0.5
    recent_large_leaps: int = 0
    recent_altered_density: float = 0.0
    recent_chord_identity_strength: float = 0.5
    ensemble_activity: float = 0.5
    next_harmony: str = ""
    previous_pitch_midi: int | None = None
    previous_interval_semitones: int | None = None
    recent_pitches: tuple[int, ...] = ()


@dataclass(frozen=True)
class StyleTendency:
    """A contextual preference, not a deterministic rule or literal lick."""
    tendency_id: str
    feature: str
    context_tags: frozenset[str] = frozenset()
    weight: float = 0.0
    confidence: float = 1.0
    provenance: tuple[str, ...] = ()
    note: str = ""


@dataclass(frozen=True)
class LegendProfile:
    profile_id: str
    display_name: str
    instrument_family: str
    era_or_school: str
    tendencies: tuple[StyleTendency, ...] = ()
    source_count: int = 0
    notes: str = ""

    def tendency_map(self) -> Mapping[str, tuple[StyleTendency, ...]]:
        out: dict[str, list[StyleTendency]] = {}
        for t in self.tendencies:
            out.setdefault(t.feature, []).append(t)
        return {k: tuple(v) for k, v in out.items()}


@dataclass(frozen=True)
class CandidateEvent:
    pitch_midi: int | None
    duration_beats: float
    onset_offset_beats: float = 0.0
    tags: frozenset[str] = frozenset()
    source_family: str = "generated"


@dataclass(frozen=True)
class CandidateScore:
    candidate: CandidateEvent
    total: float
    components: Mapping[str, float] = field(default_factory=dict)
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class LegendBlend:
    """Weighted style policies. Weights modify tendencies, never splice phrases."""
    profiles: tuple[tuple[LegendProfile, float], ...]

    def validate(self) -> None:
        if not self.profiles:
            raise ValueError("at least one profile is required")
        if any(w < 0 for _, w in self.profiles):
            raise ValueError("legend weights cannot be negative")

    def feature_bias(self, feature: str, active_tags: Sequence[str] = ()) -> float:
        self.validate()
        tags = set(active_tags)
        value = 0.0
        for profile, profile_weight in self.profiles:
            for t in profile.tendencies:
                if t.feature != feature:
                    continue
                if t.context_tags and not t.context_tags.issubset(tags):
                    continue
                value += profile_weight * t.weight * t.confidence
        return value
