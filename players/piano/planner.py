"""Small end-to-end piano comping candidate factory.

This module connects resolved Core harmonic material to the experimental comping
policy without deciding harmony locally. It intentionally creates several plausible
families/roles and lets context-sensitive evaluation choose among them.
"""
from __future__ import annotations

from dataclasses import dataclass

from music_intelligence.harmony.jazz_harmony_core import HarmonicAffordance

from .comping import (
    CompingActionType,
    InteractionRole,
    PianoCompingCandidate,
    PianoCompingContext,
)
from .voicing import (
    PianoVoicingRequest,
    generate_rootless_voicings,
    generate_shell_voicings,
)


@dataclass(frozen=True)
class PianoCompingCandidateSet:
    candidates: tuple[PianoCompingCandidate, ...]

    @property
    def sounding(self) -> tuple[PianoCompingCandidate, ...]:
        return tuple(c for c in self.candidates if c.realization is not None)

    @property
    def silent(self) -> tuple[PianoCompingCandidate, ...]:
        return tuple(c for c in self.candidates if c.realization is None)


def build_contextual_comping_candidates(
    request: PianoVoicingRequest,
    context: PianoCompingContext,
    harmonic_affordance: HarmonicAffordance | None = None,
) -> PianoCompingCandidateSet:
    """Build a small candidate slate for one immediate comping decision.

    Candidate generation stays plural. Context does not hard-select an action here;
    it only determines which plausible families/roles are worth presenting to the
    evaluator on this tick.
    """
    request.validate()
    context.validate()

    affordance_id = (
        harmonic_affordance.affordance_id
        if harmonic_affordance is not None
        else request.material.affordance_id
    )

    out: list[PianoCompingCandidate] = [
        PianoCompingCandidate(
            action_type=CompingActionType.SILENCE,
            role=InteractionRole.LAY_OUT,
            duration_beats=max(0.25, min(request.duration_beats, 1.0)),
            harmonic_affordance_id=affordance_id,
            tags=frozenset({"candidate_factory"}),
        )
    ]

    shells = generate_shell_voicings(request)
    for realization in shells:
        out.append(
            PianoCompingCandidate(
                action_type=CompingActionType.SPARSE_SUPPORT,
                role=InteractionRole.SUPPORT,
                duration_beats=request.duration_beats,
                realization=realization,
                harmonic_affordance_id=affordance_id,
                tags=frozenset({"shell", "candidate_factory"}),
            )
        )
        out.append(
            PianoCompingCandidate(
                action_type=CompingActionType.PUNCTUATION,
                role=InteractionRole.ANCHOR,
                duration_beats=min(request.duration_beats, 0.5),
                realization=realization,
                harmonic_affordance_id=affordance_id,
                tags=frozenset({"shell", "anchor", "candidate_factory"}),
            )
        )

    rootless = generate_rootless_voicings(request)
    for realization in rootless:
        if context.phrase_boundary_probability >= 0.45 or context.available_space_beats >= 0.5:
            out.append(
                PianoCompingCandidate(
                    action_type=CompingActionType.RESPONSE,
                    role=InteractionRole.ANSWER,
                    duration_beats=request.duration_beats,
                    realization=realization,
                    harmonic_affordance_id=affordance_id,
                    tags=frozenset({"rootless", "response", "candidate_factory"}),
                )
            )
        if context.section_energy >= 0.5:
            out.append(
                PianoCompingCandidate(
                    action_type=CompingActionType.SUSTAINED_SUPPORT,
                    role=InteractionRole.BUILD,
                    duration_beats=max(request.duration_beats, 0.75),
                    realization=realization,
                    harmonic_affordance_id=affordance_id,
                    tags=frozenset({"rootless", "build", "candidate_factory"}),
                )
            )

    return PianoCompingCandidateSet(tuple(out))
