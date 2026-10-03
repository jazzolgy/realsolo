"""Bridge provenance-aware Shared Vocabulary into Shared Motif Intelligence.

The bridge intentionally carries only abstract, source-grounded identity.
It never reconstructs literal phrases from prose metadata and never invents
interval/rhythm schemas that are not explicitly supplied by a verified caller.
"""
from __future__ import annotations

from music_intelligence.legends.interfaces import VocabularyMemoryItem
from .learner import MotifLearningState
from .representation import MotifCandidate, MotifIdentity, MotifSourceType


def motif_candidate_from_vocabulary(
    item: VocabularyMemoryItem,
    *,
    interval_seed: tuple[int, ...] = (),
    rhythm_seed: tuple[float, ...] = (),
    learning: MotifLearningState = MotifLearningState(),
) -> MotifCandidate:
    """Create one abstract motif candidate from a ranked vocabulary item.

    interval_seed and rhythm_seed must come from separately verified structured
    evidence. Descriptive strings in VocabularyMemoryItem are not parsed back
    into exact note sequences.
    """
    item.validate()
    learning.validate()
    if rhythm_seed and any(x <= 0 for x in rhythm_seed):
        raise ValueError("rhythm_seed must contain positive durations")

    tags = set(item.context_tags)
    interaction = ""
    if "answer" in tags:
        interaction = "answer"
    elif "ensemble_space" in tags:
        interaction = "response"

    target = item.harmonic_function or (
        "contextual_retarget"
        if "harmonic_retarget" in tags
        else ""
    )
    phrase_shape = item.phrase_position or "vocabulary_abstraction"

    identity = MotifIdentity(
        motif_id=f"vocabulary:{item.vocabulary_id}",
        interval_schema=tuple(interval_seed[:4]),
        rhythm_schema=tuple(rhythm_seed[:6]),
        contour=item.contour,
        phrase_shape=phrase_shape,
        density=.5,
        harmonic_target_behavior=target,
        tension_shape=item.tension_curve,
        interaction_function=interaction,
        event_count_hint=max(
            2,
            min(6, max(len(interval_seed) + 1, len(rhythm_seed), 3)),
        ),
        provenance=(
            "shared_vocabulary",
            item.vocabulary_id,
            item.source_id,
            *item.provenance,
        ),
    )
    candidate = MotifCandidate(
        identity=identity,
        source_type=MotifSourceType.VOCABULARY_SEEDED,
        generation_weight=max(.25, min(.78, .42 + .30 * item.confidence)),
        learned_weight=learning.source_bias(MotifSourceType.VOCABULARY_SEEDED),
        reasons=(
            "source-grounded vocabulary identity abstracted into motif memory",
            "literal phrase reconstruction intentionally disabled",
        ),
    )
    candidate.validate()
    return candidate


def motif_candidates_from_vocabulary(
    items: tuple[VocabularyMemoryItem, ...],
    *,
    limit: int = 6,
    learning: MotifLearningState = MotifLearningState(),
) -> tuple[MotifCandidate, ...]:
    if not 1 <= limit <= 16:
        raise ValueError("limit must be within 1..16")
    out = tuple(
        motif_candidate_from_vocabulary(item, learning=learning)
        for item in items[:limit]
    )
    return tuple(sorted(
        out,
        key=lambda x: (x.generation_weight, x.identity.motif_id),
        reverse=True,
    ))
