"""Shared Legend Intelligence interfaces.

Legend evidence is contextual memory/prior, not instrument ownership. Players query
this layer, then realize the result with their own policy and physical model.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Mapping, Sequence

from music_intelligence.reasoning.legend_style_core import LegendProfile, MusicalContextVector


class LegendDomain(str, Enum):
    HARMONY_TARGET_SELECTION = "harmony_target_selection"
    LINEAR_CONNECTION = "linear_connection"
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
    TENSION_RELEASE = "tension_release"
    FORM_AWARENESS = "form_awareness"
    FUTURE_HARMONY_AWARENESS = "future_harmony_awareness"
    CALL_RESPONSE = "call_response"
    ENSEMBLE_INTERACTION = "ensemble_interaction"
    HEAD_INTERPRETATION = "head_interpretation"
    PHYSICAL_BEHAVIOR = "physical_behavior"


class VocabularyCandidateFamily(str, Enum):
    LITERAL_QUOTE = "literal_quote"
    TRANSPOSED_LICK = "transposed_lick"
    ADAPTED_LICK = "adapted_lick"
    FRAGMENT_RECALL = "fragment_recall"
    ABSTRACTED_PATTERN = "abstracted_pattern"
    HYBRID_COMPOSITION = "hybrid_composition"


@dataclass(frozen=True)
class LegendQueryContext:
    musical: MusicalContextVector = MusicalContextVector()
    active_tags: frozenset[str] = frozenset()


@dataclass(frozen=True)
class LegendTendencyMatch:
    profile_id: str
    tendency_id: str
    feature: str
    weighted_bias: float
    confidence: float
    provenance: tuple[str, ...] = ()
    note: str = ""


@dataclass(frozen=True)
class LegendProfileView:
    """Domain/context query over one legend's evidence profiles.

    domain_features maps each domain to feature names already used by StyleTendency.
    It does not manufacture tendencies for uncovered domains.
    """
    legend_id: str
    profiles: tuple[tuple[LegendProfile, float], ...]
    domain_features: Mapping[LegendDomain, frozenset[str]]

    def query(
        self,
        domain: LegendDomain,
        context: LegendQueryContext = LegendQueryContext(),
    ) -> tuple[LegendTendencyMatch, ...]:
        allowed = self.domain_features.get(domain, frozenset())
        tags = set(context.active_tags)
        out: list[LegendTendencyMatch] = []
        for profile, profile_weight in self.profiles:
            for tendency in profile.tendencies:
                if tendency.feature not in allowed:
                    continue
                if tendency.context_tags and not tendency.context_tags.issubset(tags):
                    continue
                out.append(LegendTendencyMatch(
                    profile_id=profile.profile_id,
                    tendency_id=tendency.tendency_id,
                    feature=tendency.feature,
                    weighted_bias=profile_weight * tendency.weight * tendency.confidence,
                    confidence=tendency.confidence,
                    provenance=tendency.provenance,
                    note=tendency.note,
                ))
        return tuple(out)

    def coverage(self) -> Mapping[LegendDomain, int]:
        return {domain: len(self.query(domain)) for domain in LegendDomain}


@dataclass(frozen=True)
class VocabularyItem:
    vocabulary_id: str
    legend_id: str
    source_id: str
    kind: str
    candidate_families: frozenset[VocabularyCandidateFamily]
    harmony_context: str = ""
    harmonic_function: str = ""
    local_key: str = ""
    phrase_position: str = ""
    entrance: str = ""
    ending_type: str = ""
    contour: str = ""
    interval_pattern: tuple[int, ...] = ()
    rhythm_signature: tuple[float, ...] = ()
    articulation_tags: frozenset[str] = frozenset()
    register_band: str = ""
    context_tags: frozenset[str] = frozenset()
    literal_payload_ref: str | None = None
    literal_representation_hash: str | None = None
    normalized_pitch_rhythm_hash: str | None = None
    literal_similarity: float | None = None
    structural_similarity: float | None = None
    quotation_type: str = ""
    usage_count: int = 0
    recent_usage_count: int = 0
    confidence: float = 1.0
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.vocabulary_id or not self.legend_id or not self.source_id:
            raise ValueError("vocabulary_id, legend_id and source_id are required")
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
class VocabularyQuery:
    legend_id: str
    allowed_families: frozenset[VocabularyCandidateFamily] = frozenset(VocabularyCandidateFamily)
    harmony_context: str = ""
    harmonic_function: str = ""
    phrase_position: str = ""
    required_tags: frozenset[str] = frozenset()
    max_results: int = 16


@dataclass(frozen=True)
class VocabularyMatch:
    item: VocabularyItem
    contextual_fit: float
    reasons: tuple[str, ...] = ()


class VocabularyIndex:
    def __init__(self, items: Iterable[VocabularyItem] = ()):
        self._items: dict[str, VocabularyItem] = {}
        for item in items:
            self.add(item)

    def add(self, item: VocabularyItem) -> None:
        item.validate()
        if item.vocabulary_id in self._items:
            raise ValueError(f"duplicate vocabulary_id: {item.vocabulary_id}")
        self._items[item.vocabulary_id] = item

    def query(self, query: VocabularyQuery) -> tuple[VocabularyMatch, ...]:
        if query.max_results <= 0:
            return ()
        out: list[VocabularyMatch] = []
        for item in self._items.values():
            if item.legend_id != query.legend_id:
                continue
            if not item.candidate_families.intersection(query.allowed_families):
                continue
            if query.required_tags and not query.required_tags.issubset(item.context_tags):
                continue

            fit = item.confidence
            reasons: list[str] = []
            for asked, actual, weight, label in (
                (query.harmony_context, item.harmony_context, .12, "harmony"),
                (query.harmonic_function, item.harmonic_function, .12, "function"),
                (query.phrase_position, item.phrase_position, .08, "phrase_position"),
            ):
                if asked:
                    if asked == actual:
                        fit += weight
                        reasons.append(f"{label} match")
                    elif actual:
                        fit -= weight
            if item.recent_usage_count:
                fit -= min(.25, .04 * item.recent_usage_count)
                reasons.append("recent-use repetition pressure")

            out.append(VocabularyMatch(item, fit, tuple(reasons)))

        out.sort(key=lambda x: (x.contextual_fit, x.item.vocabulary_id), reverse=True)
        return tuple(out[:query.max_results])
