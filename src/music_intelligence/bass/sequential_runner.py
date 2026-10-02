"""Causal sequential runner for AI Bassist evaluation.

This module is intentionally chart-agnostic. Callers provide one HarmonicFrame
per committed bass action plus local ensemble cues. The runner:

memory snapshot
-> bass interaction intent
-> immediate candidate selection
-> performance expression
-> renderer projection
-> commit to bass memory

It never receives or returns a precomposed future bass line.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from music_intelligence.harmony.jazz_harmony_core import HarmonicFrame
from music_intelligence.reasoning.interaction_scheduler import InteractionDirective

from .immediate_realizer import (
    BassActionCandidate,
    BassContext,
    BassMode,
    choose_immediate_bass_action,
)
from .interaction_grammar import (
    BassInteractionContext,
    BassInteractionDecision,
    choose_bass_interaction_intent,
)
from .performance_memory import (
    BassCommittedAction,
    BassPerformanceMemory,
)
from .render_projection import (
    BassRenderEvent,
    project_bass_candidate_to_render_event,
)


@dataclass(frozen=True)
class BassStepInput:
    frame: HarmonicFrame
    mode: BassMode
    beat_in_measure: float
    absolute_beat: float
    phrase_boundary: bool = False
    form_boundary: bool = False
    soloist_phrase_ending: bool = False
    drum_fill_active: bool = False
    piano_fill_active: bool = False
    low_register_conflict: bool = False
    ensemble_activity: float = 0.5
    directive: InteractionDirective | None = None


@dataclass(frozen=True)
class BassStepResult:
    absolute_beat: float
    candidate: BassActionCandidate
    interaction: BassInteractionDecision
    render_event: BassRenderEvent


@dataclass
class BassSequentialRunner:
    tempo_bpm: float = 120.0
    register_low_midi: int = 28
    register_high_midi: int = 52
    memory: BassPerformanceMemory = field(default_factory=BassPerformanceMemory)

    def step(self, item: BassStepInput) -> BassStepResult:
        if self.tempo_bpm <= 0:
            raise ValueError("tempo_bpm must be positive")

        snap = self.memory.snapshot()
        interaction = choose_bass_interaction_intent(
            BassInteractionContext(
                directive=item.directive,
                memory=snap,
                phrase_boundary=item.phrase_boundary,
                form_boundary=item.form_boundary,
                next_harmony_known=item.frame.next_expected is not None,
                soloist_phrase_ending=item.soloist_phrase_ending,
                drum_fill_active=item.drum_fill_active,
                piano_fill_active=item.piano_fill_active,
                low_register_conflict=item.low_register_conflict,
            )
        )

        candidate = choose_immediate_bass_action(
            item.frame,
            BassContext(
                mode=item.mode,
                beat_in_measure=item.beat_in_measure,
                previous_pitch_midi=snap.previous_pitch_midi,
                previous_motion_semitones=snap.previous_interval_semitones,
                register_low_midi=self.register_low_midi,
                register_high_midi=self.register_high_midi,
                ensemble_activity=item.ensemble_activity,
                memory_snapshot=snap,
                interaction_decision=interaction,
            ),
        )
        render = project_bass_candidate_to_render_event(
            candidate,
            tempo_bpm=self.tempo_bpm,
        )

        self.memory.commit(BassCommittedAction(
            event=candidate.event,
            accent=candidate.expression.accent,
            sounding_length_ratio=candidate.expression.sounding_length_ratio,
            articulation=candidate.expression.articulation,
            interaction_role=interaction.intent.value,
        ))
        return BassStepResult(
            absolute_beat=item.absolute_beat,
            candidate=candidate,
            interaction=interaction,
            render_event=render,
        )

    def run(self, steps: tuple[BassStepInput, ...]) -> tuple[BassStepResult, ...]:
        out: list[BassStepResult] = []
        for step in steps:
            out.append(self.step(step))
        return tuple(out)
