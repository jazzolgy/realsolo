"""Small end-to-end piano comping candidate factory.

This module connects resolved Core harmonic material to the experimental comping
policy without deciding harmony locally. It intentionally creates several plausible
families/roles and lets context-sensitive evaluation choose among them.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

from music_intelligence.harmony.jazz_harmony_core import HarmonicAffordance

from .comping import (
    CompingActionType,
    InteractionRole,
    PianoCompingCandidate,
    PianoCompingContext,
)
from .expression import expand_expression_variants
from .candidate_diversity import select_diverse_candidates
from .ensemble_role import PianoEnsembleMode
from .harmonic_semantics import annotate_harmonic_semantics
from .rhythm import expand_rhythmic_variants
from .voicing import (
    PianoVoicingRequest,
    generate_extended_voicing_families,
    generate_rootless_voicings,
    generate_root_anchor_voicings,
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

    shells = tuple(annotate_harmonic_semantics(x) for x in generate_shell_voicings(request))
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

    root_anchors = tuple(
        annotate_harmonic_semantics(x)
        for x in generate_root_anchor_voicings(request)
    )
    for realization in root_anchors:
        out.append(
            PianoCompingCandidate(
                action_type=CompingActionType.PUNCTUATION,
                role=InteractionRole.ANCHOR,
                duration_beats=min(request.duration_beats,0.5),
                realization=realization,
                harmonic_affordance_id=affordance_id,
                tags=frozenset({"root_anchor","structural_reset","candidate_factory"}),
            )
        )

    rootless = tuple(annotate_harmonic_semantics(x) for x in generate_rootless_voicings(request))
    for realization in rootless:
        # Rootless color voicings are ordinary comping material, not only a
        # response/build effect. This keeps 9th/13th color present in normal time.
        out.append(
            PianoCompingCandidate(
                action_type=CompingActionType.SPARSE_SUPPORT,
                role=InteractionRole.SUPPORT,
                duration_beats=request.duration_beats,
                realization=realization,
                harmonic_affordance_id=affordance_id,
                tags=frozenset({"rootless", "tension_support", "candidate_factory"}),
            )
        )
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

    static_or_modal = False
    if harmonic_affordance is not None:
        tags = set(harmonic_affordance.context_tags)
        static_or_modal = bool(
            {"modal", "static_harmony", "sustained_harmony", "pedal"} & tags
        )

    if static_or_modal:
        for realization in (annotate_harmonic_semantics(x) for x in generate_extended_voicing_families(request)):
            family = realization.event.source_family.removeprefix("piano_")
            if family in {"quartal", "inverted_quartal", "mixed"}:
                role = InteractionRole.BUILD if context.section_energy >= 0.55 else InteractionRole.ANCHOR
                action = (
                    CompingActionType.SUSTAINED_SUPPORT
                    if role is InteractionRole.BUILD
                    else CompingActionType.PUNCTUATION
                )
            elif family == "octave":
                role = InteractionRole.PUNCTUATE if context.section_energy >= 0.6 else InteractionRole.SUPPORT
                action = CompingActionType.PUNCTUATION
            else:
                role = InteractionRole.SUPPORT
                action = CompingActionType.SUSTAINED_SUPPORT

            out.append(
                PianoCompingCandidate(
                    action_type=action,
                    role=role,
                    duration_beats=max(request.duration_beats, 0.5),
                    realization=realization,
                    harmonic_affordance_id=affordance_id,
                    tags=frozenset({family, "extended_family", "candidate_factory"}),
                )
            )

    if context.ensemble_mode in {
        PianoEnsembleMode.PIANO_HEAD_TRIO,
        PianoEnsembleMode.PIANO_SOLO_TRIO,
    }:
        # Add physically compact LH-only realizations so the evaluator has genuine
        # accompaniment options while RH carries melody/solo foreground.
        lh_foreground_variants: list[PianoCompingCandidate] = []
        for candidate in out:
            if candidate.realization is None:
                continue
            pitches=candidate.realization.event.pitches_midi
            if not pitches:
                continue
            if max(pitches) <= 67 and (max(pitches)-min(pitches)) <= 16:
                realization=replace(
                    candidate.realization,
                    hand_assignment=tuple(
                        (voice.voice_id,"LH")
                        for voice in candidate.realization.event.voices
                    ),
                )
                lh_foreground_variants.append(
                    replace(
                        candidate,
                        realization=realization,
                        tags=frozenset(set(candidate.tags)|{"lh_comping","foreground_support"}),
                    )
                )
        out.extend(lh_foreground_variants)

    return PianoCompingCandidateSet(tuple(out))


def expand_candidate_set_rhythmically(
    candidate_set: PianoCompingCandidateSet,
    context: PianoCompingContext,
) -> PianoCompingCandidateSet:
    """Expand sounding candidates into immediate timing alternatives.

    Silence remains one explicit candidate and is never converted into a fake event.
    """
    context.validate()
    out: list[PianoCompingCandidate] = []
    for candidate in candidate_set.candidates:
        if candidate.realization is None:
            out.append(candidate)
            continue
        variants = expand_rhythmic_variants(
            candidate,
            phrase_boundary_probability=context.phrase_boundary_probability,
            available_space_beats=context.available_space_beats,
            drummer_activity=context.drummer_activity,
        )
        out.extend(variants or (candidate,))
    return PianoCompingCandidateSet(tuple(out))


def expand_candidate_set_expressively(
    candidate_set: PianoCompingCandidateSet,
    context: PianoCompingContext,
    interaction_state,
) -> PianoCompingCandidateSet:
    """Expand sounding candidates into register/dynamic/touch alternatives."""
    context.validate()
    interaction_state.validate()
    out: list[PianoCompingCandidate] = []
    for candidate in candidate_set.candidates:
        if candidate.realization is None:
            out.append(candidate)
            continue
        foreground_register = context.soloist_register_midi
        if context.ensemble_mode in {
            PianoEnsembleMode.PIANO_HEAD_TRIO,
            PianoEnsembleMode.PIANO_SOLO_TRIO,
        } and context.piano_foreground_register_midi is not None:
            foreground_register = context.piano_foreground_register_midi

        variants = expand_expression_variants(
            candidate,
            interaction_state,
            bass_activity=context.bass_activity,
            soloist_register_midi=foreground_register,
        )
        out.extend(variants or (candidate,))
    return PianoCompingCandidateSet(tuple(out))


def build_immediate_performance_candidates(
    request: PianoVoicingRequest,
    context: PianoCompingContext,
    interaction_state,
    harmonic_affordance: HarmonicAffordance | None = None,
    *,
    include_rhythm: bool = True,
    include_expression: bool = True,
    max_candidates: int = 128,
) -> PianoCompingCandidateSet:
    """Build a bounded one-tick candidate slate.

    Pipeline:
      harmonic material -> voicing/role -> rhythmic placement -> expression

    Every result is still one immediate gesture. The cap prevents combinatorial
    explosion and is not a musical ranking of future actions.
    """
    if max_candidates < 1:
        raise ValueError("max_candidates must be positive")
    interaction_state.validate()

    slate = build_contextual_comping_candidates(
        request,
        context,
        harmonic_affordance,
    )
    if include_rhythm:
        slate = expand_candidate_set_rhythmically(slate, context)
    if include_expression:
        slate = expand_candidate_set_expressively(
            slate,
            context,
            interaction_state,
        )

    if len(slate.candidates) <= max_candidates:
        return slate

    kept = select_diverse_candidates(slate.candidates, max_candidates)
    return PianoCompingCandidateSet(kept)
