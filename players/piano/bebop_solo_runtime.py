"""End-to-end immediate bebop piano solo tick.

This composes existing evidence and policy layers while preserving one-event commitment.
"""
from __future__ import annotations

from dataclasses import dataclass

from music_intelligence.reasoning.legend_style_core import CandidateScore

from .bebop_complementarity import EnsembleComplementarityEvidence
from .bebop_harmonic_turn import BebopHarmonicTurnContext
from .bebop_phrase_intent import BebopPhraseIntent, derive_bebop_phrase_intent
from .bebop_solo_candidates import generate_immediate_bebop_candidates
from .bebop_turn_taking import BebopTurnTakingEvidence
from .solo import (
    PianoSoloContext,
    PianoSoloEvaluator,
    PianoSoloState,
    perform_one_piano_solo_event,
)
from .voicing import ResolvedHarmonicMaterial


@dataclass(frozen=True)
class BebopSoloTickPlan:
    intent: BebopPhraseIntent
    candidates: tuple

    def validate(self) -> None:
        self.intent.validate()
        if not self.candidates:
            raise ValueError("bebop solo tick must contain immediate candidates")
        for candidate in self.candidates:
            if hasattr(candidate,"future_notes") or hasattr(candidate,"phrase_sequence"):
                raise ValueError("future phrase data is not allowed in immediate candidates")


def build_bebop_solo_tick(
    *,
    current_material: ResolvedHarmonicMaterial,
    harmonic_turn: BebopHarmonicTurnContext,
    turn: BebopTurnTakingEvidence,
    complementarity: EnsembleComplementarityEvidence,
    previous_pitch_midi: int | None = None,
    next_material: ResolvedHarmonicMaterial | None = None,
    low_midi: int = 48,
    high_midi: int = 96,
) -> BebopSoloTickPlan:
    intent=derive_bebop_phrase_intent(
        harmonic_turn,
        turn,
        complementarity,
    )
    candidates=generate_immediate_bebop_candidates(
        current_material=current_material,
        next_material=next_material,
        intent=intent,
        previous_pitch_midi=previous_pitch_midi,
        low_midi=low_midi,
        high_midi=high_midi,
    )
    plan=BebopSoloTickPlan(intent,candidates)
    plan.validate()
    return plan


def perform_bebop_solo_tick(
    *,
    tick: BebopSoloTickPlan,
    evaluator: PianoSoloEvaluator,
    context: PianoSoloContext,
    state: PianoSoloState,
) -> CandidateScore:
    """Commit exactly one event from the current tick plan."""
    tick.validate()
    soft_plan=tick.intent.to_soft_plan()
    return perform_one_piano_solo_event(
        soft_plan,
        evaluator,
        tick.candidates,
        context,
        state,
    )
