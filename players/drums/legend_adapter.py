"""Drum-player adapter for Shared Legend Intelligence v2.

Shared Core owns LegendProfileView and VocabularyMemoryItem.  The drum player
only projects those shared semantics into instrument-specific candidate biases.

No named drummer is hard-coded here and no future drum phrase is frozen.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from music_intelligence.legends import (
    LegendDomain,
    LegendProfileView,
    VocabularyMemoryItem,
    VocabularyUseType,
)

from .model import DrumGesture, DrumVoice, GestureRole


class DrumLegendFeature(str, Enum):
    RIDE_SURFACE_FLEXIBILITY = "ride_surface_flexibility"
    COMPING_CONVERSATION = "comping_conversation"
    SPACE_PREFERENCE = "space_preference"
    BASS_DRUM_INTERACTIVITY = "bass_drum_interactivity"
    FORM_PUNCTUATION = "form_punctuation"
    MOTIF_DEVELOPMENT = "motif_development"
    ORCHESTRATION_MOBILITY = "orchestration_mobility"
    DYNAMIC_RESPONSIVENESS = "dynamic_responsiveness"


DRUM_LEGEND_DOMAINS: tuple[LegendDomain, ...] = (
    LegendDomain.RHYTHM_SUBDIVISION,
    LegendDomain.MICROTIMING_SWING,
    LegendDomain.ARTICULATION,
    LegendDomain.MOTIF_DEVELOPMENT,
    LegendDomain.REPETITION_VARIATION,
    LegendDomain.FORM_AWARENESS,
    LegendDomain.CALL_RESPONSE,
    LegendDomain.ENSEMBLE_INTERACTION,
    LegendDomain.LEGEND_PHYSICAL_BEHAVIOR,
)


@dataclass(frozen=True)
class DrumLegendProjection:
    """Instrument-specific view of one or more shared legend profiles."""

    legend_ids: tuple[str, ...]
    feature_biases: tuple[tuple[str, float], ...]
    active_tags: frozenset[str] = frozenset()
    provenance: tuple[str, ...] = ("shared_legend_intelligence",)

    def bias(self, feature: DrumLegendFeature | str) -> float:
        key = feature.value if isinstance(feature, DrumLegendFeature) else feature
        return sum(value for name, value in self.feature_biases if name == key)


@dataclass(frozen=True)
class DrumVocabularyIntent:
    """Current memory-use intention; not a future drum sequence."""

    vocabulary_id: str
    source_id: str
    use_type: VocabularyUseType
    rhythm_descriptor: str = ""
    articulation_descriptor: str = ""
    contour_descriptor: str = ""
    literal_similarity: float | None = None
    structural_similarity: float | None = None
    confidence: float = 1.0
    recent_usage_count: int = 0
    provenance: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.vocabulary_id or not self.source_id:
            raise ValueError("vocabulary_id and source_id are required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be within 0..1")
        for name in ("literal_similarity", "structural_similarity"):
            value = getattr(self, name)
            if value is not None and not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")


def project_legend_views(
    views: Iterable[tuple[LegendProfileView, float]],
    *,
    active_tags: Iterable[str] = (),
) -> DrumLegendProjection:
    """Project contextual shared tendencies into drummer-owned feature biases."""
    tags = tuple(active_tags)
    totals: dict[str, float] = {}
    legends: list[str] = []
    for view, view_weight in views:
        if view_weight < 0:
            raise ValueError("legend view weight may not be negative")
        legends.append(view.legend_id)
        for domain in DRUM_LEGEND_DOMAINS:
            for tendency in view.tendencies(domain=domain, active_tags=tags):
                totals[tendency.feature] = totals.get(tendency.feature, 0.0) + (
                    view_weight * tendency.weight * tendency.confidence
                )
    return DrumLegendProjection(
        legend_ids=tuple(legends),
        feature_biases=tuple(sorted(totals.items())),
        active_tags=frozenset(tags),
        provenance=("shared_legend_intelligence", "players_drums_projection"),
    )


def drum_vocabulary_intent(
    item: VocabularyMemoryItem,
    *,
    use_type: VocabularyUseType,
) -> DrumVocabularyIntent:
    """Adapt shared vocabulary memory into a drum-side *intention* only.

    Literal material stays owned by Shared Legend Intelligence.  The drummer
    receives descriptors and a source reference; exact current-event realization
    remains a separate last-moment decision.
    """
    if use_type is VocabularyUseType.LITERAL_QUOTE and not item.literal_representation:
        raise ValueError("literal quote requires literal source representation")

    intent = DrumVocabularyIntent(
        vocabulary_id=item.vocabulary_id,
        source_id=item.source_id,
        use_type=use_type,
        rhythm_descriptor=item.rhythm,
        articulation_descriptor=item.articulation,
        contour_descriptor=item.contour,
        literal_similarity=item.literal_similarity,
        structural_similarity=item.structural_similarity,
        confidence=item.confidence,
        recent_usage_count=item.recent_usage_count,
        provenance=item.provenance + ("players_drums_vocabulary_adapter",),
    )
    intent.validate()
    return intent


def vocabulary_reuse_bias(intent: DrumVocabularyIntent) -> float:
    """Small anti-overuse term; quotation is allowed, parroting is not required."""
    intent.validate()
    novelty_penalty = min(0.45, 0.06 * intent.recent_usage_count)
    confidence_reward = 0.18 * intent.confidence
    if intent.use_type is VocabularyUseType.HYBRID_COMPOSITION:
        confidence_reward += 0.08
    elif intent.use_type is VocabularyUseType.LITERAL_QUOTE:
        # Literal quoting is legitimate memory, but should not dominate merely
        # because it is literal.
        confidence_reward -= 0.03
    return confidence_reward - novelty_penalty


def legend_gesture_adjustment(
    gesture: DrumGesture,
    projection: DrumLegendProjection,
) -> tuple[float, tuple[tuple[str, float], ...]]:
    """Translate legend tendencies into current-gesture ranking adjustments."""
    gesture.validate()
    score = 0.0
    parts: list[tuple[str, float]] = []

    def add(feature: DrumLegendFeature, scale: float, label: str) -> None:
        nonlocal score
        value = scale * projection.bias(feature)
        if value:
            score += value
            parts.append((label, value))

    tags = gesture.tags
    voices = {hit.voice for hit in gesture.hits}

    if DrumVoice.RIDE in voices or "ride_continuity" in tags:
        add(DrumLegendFeature.RIDE_SURFACE_FLEXIBILITY, 0.28, "legend_ride_surface")

    if "snare_phrase" in tags or DrumVoice.SNARE in voices:
        add(DrumLegendFeature.COMPING_CONVERSATION, 0.24, "legend_comping_conversation")

    if gesture.role is GestureRole.SPACE or "intentional_non_response" in tags:
        add(DrumLegendFeature.SPACE_PREFERENCE, 0.30, "legend_space_preference")

    if DrumVoice.BASS_DRUM in voices:
        add(DrumLegendFeature.BASS_DRUM_INTERACTIVITY, 0.24, "legend_bass_drum")

    if gesture.role in {GestureRole.SETUP, GestureRole.ACCENT} or "punctuate" in tags:
        add(DrumLegendFeature.FORM_PUNCTUATION, 0.26, "legend_form_punctuation")

    if tags.intersection({
        "return", "displaced_return", "variation", "repeat", "recap",
        "motif", "drum_solo",
    }):
        add(DrumLegendFeature.MOTIF_DEVELOPMENT, 0.24, "legend_motif_development")

    if voices.intersection({
        DrumVoice.HIGH_TOM,
        DrumVoice.MID_TOM,
        DrumVoice.FLOOR_TOM,
        DrumVoice.CRASH,
    }):
        add(DrumLegendFeature.ORCHESTRATION_MOBILITY, 0.20, "legend_orchestration")

    return score, tuple(parts)
