"""Head-melody interpretation for piano-led trio.

Preserves the written melody event while allowing current-event timing/duration
reinterpretation. This does not create or store a replacement melody.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

from music_intelligence.reasoning.legend_style_core import CandidateEvent
from music_intelligence.reasoning.head_fidelity import (
    HeadFidelityContext,
    HeadFidelityMode,
    enforce_head_fidelity,
    generate_head_candidate_variants,
)
from music_intelligence.reasoning.hierarchical_priors import HierarchicalPriorSet
from music_intelligence.reasoning.contextual_prior_gating import (
    gated_prior_set,
    head_gating_context,
)

from .rh_swing import RHSwingContext, SwingRole, apply_rh_swing


@dataclass(frozen=True)
class HeadInterpretationContext:
    tempo_bpm: float = 130.0
    subdivision_phase: float = 0.0
    phrase_maturity: float = 0.5
    phrase_end_pressure: float = 0.0
    next_harmony_known: bool = False
    bass_activity: float = 0.5
    drummer_activity: float = 0.5
    ensemble_density: float = 0.5
    fidelity_mode: HeadFidelityMode = HeadFidelityMode.NATURAL
    strong_beat: bool = False
    phrase_anchor: bool = False
    previous_written_pitch_midi: int | None = None
    next_written_pitch_midi: int | None = None
    harmonic_pitch_classes: frozenset[int] = frozenset()

    def validate(self) -> None:
        if not 40 <= self.tempo_bpm <= 360:
            raise ValueError("tempo_bpm outside supported range")
        for pitch in (self.previous_written_pitch_midi, self.next_written_pitch_midi):
            if pitch is not None and not 0 <= pitch <= 127:
                raise ValueError("written melody pitch must be in MIDI range")
        if any(not 0 <= pc <= 11 for pc in self.harmonic_pitch_classes):
            raise ValueError("harmonic_pitch_classes must be within 0..11")
        for name in (
            "subdivision_phase",
            "phrase_maturity",
            "phrase_end_pressure",
            "bass_activity",
            "drummer_activity",
            "ensemble_density",
        ):
            value=getattr(self,name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")


def interpret_head_event(
    written_event: CandidateEvent,
    context: HeadInterpretationContext,
) -> CandidateEvent:
    """Interpret one written melody event rather than replay it mechanically."""
    context.validate()
    tags=set(written_event.tags)|{"head_melody","melody_structural"}

    event=replace(written_event,tags=frozenset(tags))
    event=apply_rh_swing(
        event,
        RHSwingContext(
            tempo_bpm=context.tempo_bpm,
            role=SwingRole.HEAD,
            subdivision_phase=context.subdivision_phase,
            phrase_maturity=context.phrase_maturity,
            phrase_end_pressure=context.phrase_end_pressure,
            anticipation_strength=.55 if context.next_harmony_known else .0,
            confidence=.9,
        ),
    )

    onset=event.onset_offset_beats
    duration=event.duration_beats
    tags=set(event.tags)

    # Leave more air when the trio is already active; do not simply shorten every note.
    if context.ensemble_density >= .72 and duration <= .75:
        duration *= .90
        tags.add("head_leave_space")

    # Phrase endings can be more vocal/elastic, especially against active bass/drums.
    if context.phrase_end_pressure >= .7:
        duration *= 1.10
        onset += .015
        tags.add("head_vocal_ending")

    # Long structural tones can breathe while rhythm section carries time.
    if written_event.duration_beats >= 1.0 and (
        context.bass_activity >= .45 or context.drummer_activity >= .45
    ):
        duration *= 1.08
        tags.add("head_rhythm_section_carried")

    proposed = replace(
        event,
        onset_offset_beats=onset,
        duration_beats=max(.0625,duration),
        tags=frozenset(tags),
    )
    return enforce_head_fidelity(
        written_event,
        proposed,
        HeadFidelityContext(
            mode=context.fidelity_mode,
            strong_beat=context.strong_beat,
            phrase_anchor=context.phrase_anchor,
            phrase_end=context.phrase_end_pressure >= .7,
            previous_written_pitch_midi=context.previous_written_pitch_midi,
            next_written_pitch_midi=context.next_written_pitch_midi,
            harmonic_pitch_classes=context.harmonic_pitch_classes,
        ),
    )


def head_event_candidates(
    written_event: CandidateEvent,
    context: HeadInterpretationContext,
) -> tuple[CandidateEvent, ...]:
    """Return conservative head alternatives around the written melody event.

    The written pitch remains the reference.  NATURAL mode permits only local
    rhythmic repeat/split and nearby ornament candidates on unprotected notes.
    """
    context.validate()
    base = interpret_head_event(written_event, context)
    variants = generate_head_candidate_variants(
        base,
        HeadFidelityContext(
            mode=context.fidelity_mode,
            strong_beat=context.strong_beat,
            phrase_anchor=context.phrase_anchor,
            phrase_end=context.phrase_end_pressure >= .7,
            previous_written_pitch_midi=context.previous_written_pitch_midi,
            next_written_pitch_midi=context.next_written_pitch_midi,
            harmonic_pitch_classes=context.harmonic_pitch_classes,
        ),
    )
    return variants


def gated_head_prior_hierarchy(
    priors: HierarchicalPriorSet | None,
    context: HeadInterpretationContext,
) -> HierarchicalPriorSet | None:
    """Attenuate improvisation priors behind written-head fidelity."""

    context.validate()
    return gated_prior_set(
        priors,
        head_gating_context(
            mode=context.fidelity_mode.value,
            ensemble_complexity=context.ensemble_density,
            live_context_confidence=max(
                context.phrase_end_pressure,
                .8 if context.strong_beat or context.phrase_anchor else .5,
            ),
        ),
    )
