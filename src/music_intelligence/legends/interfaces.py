"""Generic Legend Intelligence interfaces.

Legend research, vocabulary memory, style grammar, and instrument realization are
separate concerns.  Player packages consume these interfaces; they do not own a
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


@dataclass(frozen=True)
class VocabularyQuery:
    legend_id: str
    domain: LegendDomain | None = None
    harmony_context: str = ""
    local_key: str = ""
    phrase_position: str = ""
    context_tags: frozenset[str] = frozenset()
    allowed_uses: frozenset[VocabularyUseType] = frozenset(VocabularyUseType)
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
    literal_representation_hash: str = ""
    normalized_pitch_rhythm_hash: str = ""
    literal_similarity: float | None = None
    structural_similarity: float | None = None
    quotation_type: VocabularyUseType | None = None
    usage_count: int = 0
    recent_usage_count: int = 0
    confidence: float = 1.0
    provenance: tuple[str, ...] = ()


@dataclass(frozen=True)
class LegendProfileView:
    """Context/query view over one legend profile.

    The view exposes conditional tendencies.  It does not expose future note
    sequences and does not imply that the consuming instrument owns the legend.
    """

    legend_id: str
    profile: LegendProfile
    domain_features: Mapping[LegendDomain, tuple[str, ...]]

    def tendencies(
        self,
        *,
        domain: LegendDomain | None = None,
        active_tags: Sequence[str] = (),
    ) -> tuple[StyleTendency, ...]:
        tags = set(active_tags)
        allowed = None if domain is None else set(self.domain_features.get(domain, ()))
        out = []
        for tendency in self.profile.tendencies:
            if allowed is not None and tendency.feature not in allowed:
                continue
            if tendency.context_tags and not tendency.context_tags.issubset(tags):
                continue
            out.append(tendency)
        return tuple(out)

    def blend(self, weight: float = 1.0) -> LegendBlend:
        return LegendBlend(((self.profile, weight),))


class VocabularyProvider(Protocol):
    """Instrument-neutral vocabulary memory provider."""

    def query(self, request: VocabularyQuery) -> tuple[VocabularyMemoryItem, ...]:
        ...
