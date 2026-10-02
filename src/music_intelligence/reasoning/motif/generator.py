"""Shared Motif Generator.

Generates abstract motif identities from musical context. It does not schedule
exact future notes.
"""
from __future__ import annotations
from dataclasses import dataclass

from .learner import MotifLearningState
from .representation import MotifCandidate, MotifIdentity, MotifSourceType


@dataclass(frozen=True)
class MotifGenerationContext:
    tension: float = 0.0
    ensemble_activity: float = .5
    phrase_space: float = .25
    future_harmony_available: bool = False
    interaction_role: str = ""
    rhythmic_seed: tuple[float, ...] = ()
    interval_seed: tuple[int, ...] = ()
    contour_seed: str = ""
    vocabulary_seed_id: str = ""
    ensemble_seed_id: str = ""
    active_motif_id: str = ""
    max_candidates: int = 6

    def validate(self) -> None:
        for name in ("tension", "ensemble_activity", "phrase_space"):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")
        if not 1 <= self.max_candidates <= 16:
            raise ValueError("max_candidates must be within 1..16")
        if self.rhythmic_seed and any(x <= 0 for x in self.rhythmic_seed):
            raise ValueError("rhythmic_seed must be positive")


def _candidate(
    motif_id: str,
    source: MotifSourceType,
    *,
    interval_schema: tuple[int, ...] = (),
    rhythm_schema: tuple[float, ...] = (),
    contour: str = "",
    phrase_shape: str = "",
    density: float = .5,
    harmonic_target_behavior: str = "",
    tension_shape: str = "",
    interaction_function: str = "",
    provenance: tuple[str, ...] = (),
    weight: float = .5,
    learning: MotifLearningState,
    reason: str,
) -> MotifCandidate:
    identity = MotifIdentity(
        motif_id=motif_id,
        interval_schema=interval_schema,
        rhythm_schema=rhythm_schema,
        contour=contour,
        phrase_shape=phrase_shape,
        density=max(0.0, min(1.0, density)),
        harmonic_target_behavior=harmonic_target_behavior,
        tension_shape=tension_shape,
        interaction_function=interaction_function,
        event_count_hint=max(2, min(6, max(len(interval_schema) + 1, len(rhythm_schema), 3))),
        provenance=provenance,
    )
    out = MotifCandidate(
        identity=identity,
        source_type=source,
        generation_weight=max(0.0, min(1.0, weight)),
        learned_weight=learning.source_bias(source),
        reasons=(reason,),
    )
    out.validate()
    return out


def generate_motif_candidates(
    context: MotifGenerationContext,
    learning: MotifLearningState = MotifLearningState(),
) -> tuple[MotifCandidate, ...]:
    context.validate()
    learning.validate()
    out: list[MotifCandidate] = []

    # A small generative-new candidate is always available.
    base_rhythm = context.rhythmic_seed or ((.5, .5, 1.0) if context.tension < .7 else (.5, .5, .5, .5))
    base_intervals = context.interval_seed or ((2, 1) if context.tension < .65 else (3, -1, 2))
    out.append(_candidate(
        "generated:new",
        MotifSourceType.GENERATIVE_NEW,
        interval_schema=tuple(base_intervals[:4]),
        rhythm_schema=tuple(base_rhythm[:5]),
        contour=context.contour_seed or ("rising" if sum(base_intervals) > 0 else "mixed"),
        phrase_shape="compact_cell",
        density=.42 + .30 * context.tension,
        harmonic_target_behavior="next_harmony" if context.future_harmony_available else "current_field",
        tension_shape="rising" if context.tension >= .6 else "open",
        interaction_function=context.interaction_role.lower(),
        provenance=("shared_generator",),
        weight=.56,
        learning=learning,
        reason="new compact identity from current context",
    ))

    if context.vocabulary_seed_id:
        out.append(_candidate(
            f"vocabulary:{context.vocabulary_seed_id}",
            MotifSourceType.VOCABULARY_SEEDED,
            interval_schema=tuple(context.interval_seed[:4]),
            rhythm_schema=tuple(context.rhythmic_seed[:5]),
            contour=context.contour_seed,
            phrase_shape="vocabulary_abstraction",
            density=.5,
            harmonic_target_behavior="contextual_retarget",
            provenance=("shared_vocabulary", context.vocabulary_seed_id),
            weight=.62,
            learning=learning,
            reason="vocabulary seed abstracted without forcing literal phrase",
        ))

    if context.ensemble_seed_id:
        out.append(_candidate(
            f"ensemble:{context.ensemble_seed_id}",
            MotifSourceType.ENSEMBLE_DERIVED,
            rhythm_schema=tuple(context.rhythmic_seed[:5]) or (.5, 1.0, .5),
            contour=context.contour_seed,
            phrase_shape="response_cell",
            density=max(.2, .55 - .25 * context.ensemble_activity),
            interaction_function=context.interaction_role.lower() or "response",
            provenance=("ensemble_observation", context.ensemble_seed_id),
            weight=.64 if context.interaction_role.upper() == "ANSWER" else .50,
            learning=learning,
            reason="motif identity derived from ensemble event",
        ))

    if context.active_motif_id:
        out.append(_candidate(
            f"memory:{context.active_motif_id}",
            MotifSourceType.SELF_MEMORY_DERIVED,
            interval_schema=tuple(context.interval_seed[:3]),
            rhythm_schema=tuple(context.rhythmic_seed[:4]),
            contour=context.contour_seed,
            phrase_shape="self_recall",
            density=.45,
            harmonic_target_behavior="contextual_retarget",
            provenance=("self_memory", context.active_motif_id),
            weight=.60,
            learning=learning,
            reason="active motif identity recalled for development",
        ))

    if context.vocabulary_seed_id and context.ensemble_seed_id:
        out.append(_candidate(
            f"hybrid:{context.vocabulary_seed_id}:{context.ensemble_seed_id}",
            MotifSourceType.HYBRID,
            interval_schema=tuple(context.interval_seed[:3]),
            rhythm_schema=tuple(context.rhythmic_seed[:5]),
            contour=context.contour_seed,
            phrase_shape="hybrid_cell",
            density=.5,
            harmonic_target_behavior="contextual_retarget",
            interaction_function=context.interaction_role.lower(),
            provenance=("shared_vocabulary", context.vocabulary_seed_id, "ensemble_observation", context.ensemble_seed_id),
            weight=.66,
            learning=learning,
            reason="hybrid combines vocabulary identity with current ensemble behavior",
        ))

    ranked = sorted(
        out,
        key=lambda x: (x.generation_weight + .18 * x.learned_weight, x.identity.motif_id),
        reverse=True,
    )
    return tuple(ranked[:context.max_candidates])
