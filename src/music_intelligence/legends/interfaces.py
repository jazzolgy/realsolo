"""Generic Legend Intelligence interfaces.

Legend research, vocabulary memory, style grammar, and instrument realization are
separate concerns. Player packages consume these interfaces; they do not own a
specific legend profile.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Protocol, Sequence

from music_intelligence.reasoning.legend_style_core import LegendBlend, LegendProfile, StyleTendency


class LegendDomain(str, Enum):
    HARMONY_TARGET_SELECTION = "harmony_target_selection"
    LINEAR_CONNECTION = "linear_connection"
    TENSION_RELEASE = "tension_release"
    FUTURE_HARMONY_AWARENESS = "future_harmony_awareness"
    PHRASE_ENTRANCE = "phrase_entrance"
    PHRASE_ENDING = "phrase_ending"
    BREATH_SPACE = "breath_space"
    RHYTHM_SUBDIVISION = "rhythm_subdivision"
    MICROTIMING_SWING = "microtiming_swing"
    REGISTER_TRAJECTORY = "register_trajectory"
    INTERVAL_LEAP_GRAMMAR = "interval_leap_grammar"
    ARTICULATION = "articulation"
    MOTIF_DEVELOPMENT = "motif_development"
    REPETITION_VARIATION = "repetition_variation"
    HEAD_INTERPRETATION = "head_interpretation"
    FORM_AWARENESS = "form_awareness"
    CALL_RESPONSE = "call_response"
    ENSEMBLE_INTERACTION = "ensemble_interaction"
    LEGEND_PHYSICAL_BEHAVIOR = "legend_physical_behavior"


class VocabularyUseType(str, Enum):
    LITERAL_QUOTE = "literal_quote"
    TRANSPOSED_LICK = "transposed_lick"
    ADAPTED_LICK = "adapted_lick"
    FRAGMENT_RECALL = "fragment_recall"
    ABSTRACTED_PATTERN = "abstracted_pattern"
    HYBRID_COMPOSITION = "hybrid_composition"


class VocabularyDimension(str, Enum):
    """Instrument-neutral dimensions that may transfer across players."""

    PITCH_INTERVAL = "pitch_interval"
    RHYTHM = "rhythm"
    CONTOUR = "contour"
    ACCENT = "accent"
    DENSITY_ARC = "density_arc"
    PHRASE_SHAPE = "phrase_shape"
    TENSION_RELEASE = "tension_release"
    TARGET_BEHAVIOR = "target_behavior"
    INTERACTION_ROLE = "interaction_role"
    ARTICULATION = "articulation"
    REGISTER_TRAJECTORY = "register_trajectory"


@dataclass(frozen=True)
class VocabularyQuery:
    legend_id: str
    domain: LegendDomain | None = None
    harmony_context: str = ""
    harmonic_function: str = ""
    local_key: str = ""
    phrase_position: str = ""
    context_tags: frozenset[str] = frozenset()
    allowed_uses: frozenset[VocabularyUseType] = frozenset(VocabularyUseType)
    required_dimensions: frozenset[VocabularyDimension] = frozenset()
    target_instrument: str = ""
    limit: int = 16


@dataclass(frozen=True)
class VocabularyMemoryItem:
    vocabulary_id: str
    source_id: str
    recording_id: str = ""
    tune_id: str = ""
    chorus: str = ""
    bar: str = ""
    timestamp: str = ""
    literal_representation: str = ""
    transposition_normalized_representation: str = ""
    harmony_context: str = ""
    local_key: str = ""
    harmonic_function: str = ""
    phrase_position: str = ""
    entrance: str = ""
    ending: str = ""
    rhythm: str = ""
    contour: str = ""
    interval_pattern: str = ""
    articulation: str = ""
    register: str = ""
    tension_curve: str = ""
    source_instrument: str = ""
    dimensions: frozenset[VocabularyDimension] = frozenset()
    transferable_to: frozenset[str] = frozenset()
    domains: frozenset[LegendDomain] = frozenset()
    context_tags: frozenset[str] = frozenset()
    candidate_uses: frozenset[VocabularyUseType] = frozenset(VocabularyUseType)
    literal_representation_hash: str = ""
    normalized_pitch_rhythm_hash: str = ""
    literal_similarity: float | None = None
    structural_similarity: float | None = None
    quotation_type: VocabularyUseType | None = None
    usage_count: int = 0
    recent_usage_count: int = 0
    confidence: float = 1.0
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.vocabulary_id or not self.source_id:
            raise ValueError("vocabulary_id and source_id are required")
        if not self.candidate_uses:
            raise ValueError("candidate_uses may not be empty")
        if self.transferable_to and self.source_instrument in self.transferable_to:
            # This is valid, but keep the field semantic explicit: it lists allowed
            # consumers, not ownership.
            pass
        for value, name in (
            (self.literal_similarity, "literal_similarity"),
            (self.structural_similarity, "structural_similarity"),
        ):
            if value is not None and not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within 0..1")
        if self.usage_count < 0 or self.recent_usage_count < 0:
            raise ValueError("usage counts may not be negative")


@dataclass(frozen=True)
class LegendProfileView:
    """Context/query view over one legend's evidence profiles.

    profile remains the primary contextual profile for backward compatibility.
    additional_profiles carries bounded score/statistical evidence. The view
    never owns an instrument and never exposes a frozen future note sequence.
    """

    legend_id: str
    profile: LegendProfile
    domain_features: Mapping[LegendDomain, tuple[str, ...]]
    additional_profiles: tuple[tuple[LegendProfile, float], ...] = ()

    def weighted_profiles(self) -> tuple[tuple[LegendProfile, float], ...]:
        return ((self.profile, 1.0),) + self.additional_profiles

    def tendencies(
        self,
        *,
        domain: LegendDomain | None = None,
        active_tags: Sequence[str] = (),
    ) -> tuple[StyleTendency, ...]:
        tags = set(active_tags)
        allowed = None if domain is None else set(self.domain_features.get(domain, ()))
        out: list[StyleTendency] = []
        for profile, _weight in self.weighted_profiles():
            for tendency in profile.tendencies:
                if allowed is not None and tendency.feature not in allowed:
                    continue
                if tendency.context_tags and not tendency.context_tags.issubset(tags):
                    continue
                out.append(tendency)
        return tuple(out)

    def blend(self, weight: float = 1.0) -> LegendBlend:
        if weight < 0:
            raise ValueError("legend weight cannot be negative")
        return LegendBlend(tuple(
            (profile, profile_weight * weight)
            for profile, profile_weight in self.weighted_profiles()
        ))

    def coverage(self) -> Mapping[LegendDomain, int]:
        return {domain: len(self.tendencies(domain=domain)) for domain in LegendDomain}


class VocabularyProvider(Protocol):
    """Instrument-neutral vocabulary memory provider."""

    def query(self, request: VocabularyQuery) -> tuple[VocabularyMemoryItem, ...]:
        ...
