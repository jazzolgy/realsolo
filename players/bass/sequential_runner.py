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
from music_intelligence.legends.interfaces import LegendProfileView

from .ghost_notes import (
    BassGhostContext,
    BassGhostDecision,
    choose_walking_ghost_note,
    commit_walking_ghost,
)
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
from .phrase_intent import (
    BassPhraseContext,
    BassPhraseIntent,
    BassPhraseState,
    choose_bass_phrase_intent,
)
from .scorebook_evidence import BassScoreEvidenceDirective
from .solo_method import bass_shared_solo_options
from .solo_runtime import (
    BassSoloMemory,
    BassSoloPlan,
    choose_bass_solo_plan,
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
    phrase_progress: float | None = None
    local_key_pitch_classes: frozenset[int] = frozenset()
    score_evidence: BassScoreEvidenceDirective = BassScoreEvidenceDirective()
    directive: InteractionDirective | None = None
    legend_profile: LegendProfileView | None = None


@dataclass(frozen=True)
class BassStepResult:
    absolute_beat: float
    candidate: BassActionCandidate
    interaction: BassInteractionDecision
    render_event: BassRenderEvent | None
    phrase_intent: BassPhraseIntent
    solo_plan: BassSoloPlan | None = None


@dataclass
class BassSequentialRunner:
    tempo_bpm: float = 120.0
    register_low_midi: int = 28
    register_high_midi: int = 52
    memory: BassPerformanceMemory = field(default_factory=BassPerformanceMemory)
    phrase_state: BassPhraseState = field(default_factory=BassPhraseState)
    solo_memory: BassSoloMemory = field(default_factory=BassSoloMemory)
    last_interaction: BassInteractionDecision | None = None
    last_ghost_opportunity: float = 0.0

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
                ensemble_activity=item.ensemble_activity,
            )
        )

        phrase_intent = choose_bass_phrase_intent(
            BassPhraseContext(
                memory=snap,
                interaction=interaction,
                phrase_boundary=item.phrase_boundary,
                form_boundary=item.form_boundary,
                soloist_phrase_ending=item.soloist_phrase_ending,
                phrase_progress=item.phrase_progress,
                ensemble_activity=item.ensemble_activity,
            ),
            previous=self.phrase_state.current,
            actions_under_previous=self.phrase_state.committed_under_intent,
        )
        if phrase_intent != self.phrase_state.current:
            self.phrase_state.replace(phrase_intent)

        solo_plan: BassSoloPlan | None = None
        solo_snapshot = self.solo_memory.snapshot()
        if item.mode is BassMode.SOLO:
            options = bass_shared_solo_options(
                BassPhraseContext(
                    memory=snap,
                    interaction=interaction,
                    phrase_boundary=item.phrase_boundary,
                    form_boundary=item.form_boundary,
                    soloist_phrase_ending=item.soloist_phrase_ending,
                    phrase_progress=item.phrase_progress,
                    ensemble_activity=item.ensemble_activity,
                ),
                phrase_intent,
                recent_repetition_count=solo_snapshot.repetition_count,
                future_harmony_available=item.frame.next_expected is not None,
                legend_profile=item.legend_profile,
            )
            solo_plan = choose_bass_solo_plan(
                options,
                solo_snapshot,
                phrase_direction=phrase_intent.direction.value,
            )

        self.last_interaction = interaction

        candidate = choose_immediate_bass_action(
            item.frame,
            BassContext(
                mode=item.mode,
                beat_in_measure=item.beat_in_measure,
                previous_pitch_midi=snap.previous_pitch_midi,
                previous_motion_semitones=snap.previous_interval_semitones,
                register_low_midi=self.register_low_midi,
                register_high_midi=(
                    max(self.register_high_midi, 64)
                    if item.mode is BassMode.SOLO
                    else self.register_high_midi
                ),
                ensemble_activity=item.ensemble_activity,
                memory_snapshot=snap,
                interaction_decision=interaction,
                local_key_pitch_classes=item.local_key_pitch_classes,
                score_evidence=item.score_evidence,
                phrase_intent=phrase_intent,
                solo_plan=solo_plan,
                solo_snapshot=solo_snapshot,
            ),
        )
        self.last_ghost_opportunity = candidate.expression.ghost_opportunity
        render = (
            project_bass_candidate_to_render_event(
                candidate,
                tempo_bpm=self.tempo_bpm,
            )
            if candidate.event.pitch_midi is not None
            else None
        )

        self.memory.commit(BassCommittedAction(
            event=candidate.event,
            accent=candidate.expression.accent,
            sounding_length_ratio=candidate.expression.sounding_length_ratio,
            articulation=candidate.expression.articulation,
            interaction_role=interaction.intent.value,
            harmonic_role=candidate.harmonic_role.value,
            metric_role=candidate.grammar.metric_role.value,
        ))
        if item.mode is BassMode.SOLO and solo_plan is not None:
            self.solo_memory.commit(candidate.event, solo_plan.operation)

        self.phrase_state.commit()
        return BassStepResult(
            absolute_beat=item.absolute_beat,
            candidate=candidate,
            interaction=interaction,
            render_event=render,
            phrase_intent=phrase_intent,
            solo_plan=solo_plan,
        )


    def ghost_step(
        self,
        *,
        beat_in_measure: float,
        absolute_beat: float,
        mode: BassMode = BassMode.WALKING,
        ensemble_activity: float = 0.5,
        groove=None,
    ) -> BassGhostDecision:
        """Commit at most one percussive ghost event at the current offbeat.

        This path never chooses a harmonic pitch. It uses the previous physical
        string/pitch only as a renderer reference while memory records an
        unpitched event, so walking contour and voice leading remain intact.
        """
        decision = choose_walking_ghost_note(BassGhostContext(
            mode=mode.value,
            beat_in_measure=beat_in_measure,
            meter_numerator=4,
            tempo_bpm=self.tempo_bpm,
            groove=groove,
            memory=self.memory.snapshot(),
            interaction=self.last_interaction,
            ensemble_activity=ensemble_activity,
            opportunity_hint=self.last_ghost_opportunity,
        ))
        if decision.play:
            commit_walking_ghost(self.memory, decision)
        return decision

    def run(self, steps: tuple[BassStepInput, ...]) -> tuple[BassStepResult, ...]:
        out: list[BassStepResult] = []
        for step in steps:
            out.append(self.step(step))
        return tuple(out)
