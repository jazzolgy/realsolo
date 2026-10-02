from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from music_intelligence.bass import (
    BassCommittedAction,
    BassContext,
    BassInteractionContext,
    BassMode,
    BassPerformanceMemory,
    choose_bass_interaction_intent,
    choose_immediate_bass_action,
)
from music_intelligence.drums import (
    DrummerPerformanceMemory,
    DrummerRuntimeContext,
    DrummerSoftPlan,
    DrumVoice,
    TimeFeel,
    perform_one_gesture,
)
from music_intelligence.reasoning.legend_style_core import MusicalContextVector
from music_intelligence.reasoning.online_improviser import SoftPlan
from players.piano import (
    PianoCompingContext,
    PianoCompingEvaluator,
    PianoCompingState,
    PianoVoicingRequest,
    build_immediate_performance_candidates,
    perform_one_comping_action,
)

from .player_contract import RenderGesture, RenderVoice
from .trio_adapters import NativeImmediateResult


_DRUM_MIDI = {
    DrumVoice.RIDE: 51,
    DrumVoice.CLOSED_HIHAT: 42,
    DrumVoice.OPEN_HIHAT: 46,
    DrumVoice.SNARE: 38,
    DrumVoice.BASS_DRUM: 36,
    DrumVoice.CRASH: 49,
    DrumVoice.HIGH_TOM: 50,
    DrumVoice.MID_TOM: 47,
    DrumVoice.FLOOR_TOM: 43,
    DrumVoice.COWBELL: 56,
    DrumVoice.CLAVE: 75,
}


def _ms_to_beats(ms: float, tempo_bpm: float) -> float:
    return (ms / 1000.0) * tempo_bpm / 60.0


def _latest_other_phrase_maturity(snapshot, player_id: str) -> float:
    values = [
        x.phrase_maturity
        for x in snapshot.intents
        if x.player_id != player_id
    ]
    return max(values, default=0.0)


def _soloist_activity(snapshot) -> float:
    soloist_ids = {
        p.player_id
        for p in snapshot.players
        if p.role.value in {"soloist", "melody", "leader"}
    }
    values = [
        max(i.density, i.energy, i.leadership)
        for i in snapshot.intents
        if i.player_id in soloist_ids
    ]
    return max(values, default=0.0)


@dataclass
class BassNativeDecider:
    memory: BassPerformanceMemory = BassPerformanceMemory()
    mode: BassMode = BassMode.WALKING

    def __call__(self, context: Mapping[str, object]) -> NativeImmediateResult | None:
        frame = context.get("harmonic_frame")
        if frame is None:
            return None

        snapshot = context["ensemble_snapshot"]
        directive = context["interaction_directive"]
        memory_snapshot = self.memory.snapshot()
        beat = float(snapshot.transport.beat) % snapshot.transport.meter_numerator

        interaction = choose_bass_interaction_intent(BassInteractionContext(
            directive=directive,
            memory=memory_snapshot,
            phrase_boundary=_latest_other_phrase_maturity(snapshot, "bass") >= .82,
            form_boundary=snapshot.transport.form_position >= .96,
            next_harmony_known=getattr(frame, "next_expected", None) is not None,
            soloist_phrase_ending=_latest_other_phrase_maturity(snapshot, "bass") >= .72,
            drum_fill_active=any(
                i.player_id == "drums" and i.interaction.value in {"setup", "answer", "build"}
                for i in snapshot.intents
            ),
            piano_fill_active=any(
                i.player_id == "piano" and i.interaction.value in {"answer", "build", "punctuate"}
                for i in snapshot.intents
            ),
        ))

        previous = memory_snapshot.previous_pitch_midi
        bctx = BassContext(
            mode=self.mode,
            beat_in_measure=beat,
            meter_numerator=snapshot.transport.meter_numerator,
            previous_pitch_midi=previous,
            previous_motion_semitones=memory_snapshot.previous_interval_semitones,
            ensemble_activity=snapshot.ensemble_density,
            memory_snapshot=memory_snapshot,
            interaction_decision=interaction,
        )
        chosen = choose_immediate_bass_action(frame, bctx)
        if chosen.event.pitch_midi is None:
            return None

        expr = chosen.expression
        velocity = int(round(42 + 72 * expr.accent))
        duration = chosen.event.duration_beats * expr.sounding_length_ratio
        onset = chosen.event.onset_offset_beats + _ms_to_beats(
            expr.microtiming_ms, snapshot.transport.tempo_bpm
        )
        gesture = RenderGesture(
            role="bass",
            voices=(RenderVoice(
                chosen.event.pitch_midi,
                max(1, min(127, velocity)),
                max(.08, duration),
                onset,
                articulation=(expr.articulation.value,),
                instrument_role="bass",
            ),),
            source="player/bass:immediate_realizer",
            tags=tuple(sorted(set(chosen.event.tags) | {
                chosen.harmonic_role.value,
                interaction.intent.value,
            })),
            annotations={
                "bass_score": f"{chosen.score:.4f}",
                "harmonic_role": chosen.harmonic_role.value,
            },
        )

        self.memory.commit(BassCommittedAction(
            event=chosen.event,
            accent=expr.accent,
            sounding_length_ratio=expr.sounding_length_ratio,
            articulation=expr.articulation,
            interaction_role=interaction.intent.value,
        ))

        density = max(.15, min(.8, .45 + interaction.density_delta))
        energy = max(.15, min(.9, .45 + expr.accent * .35))
        return NativeImmediateResult(
            gesture=gesture,
            density=density,
            energy=energy,
            tension=min(1.0, float(getattr(frame, "tension", .5))),
            leadership=.08,
            phrase_maturity=0.0,
            tags=frozenset({
                "walking_bass" if self.mode is BassMode.WALKING else self.mode.value,
                interaction.intent.value,
                chosen.harmonic_role.value,
            }),
            provenance=("bass_immediate_realizer",),
        )


@dataclass
class DrumsNativeDecider:
    memory: DrummerPerformanceMemory = DrummerPerformanceMemory()
    feel: TimeFeel = TimeFeel.SWING

    def __call__(self, context: Mapping[str, object]) -> NativeImmediateResult | None:
        snapshot = context["ensemble_snapshot"]
        directive = context["interaction_directive"]
        beat = float(snapshot.transport.beat) % snapshot.transport.meter_numerator
        phrase_position = _latest_other_phrase_maturity(snapshot, "drums")
        energy = max(0.0, min(1.0, snapshot.ensemble_energy + directive.energy_delta))

        plan = DrummerSoftPlan(
            feel=self.feel,
            energy=energy,
            comping_density=max(.12, min(.82, .34 + directive.density_delta)),
            interaction_intent=directive.interaction.value,
            ride_velocity=int(round(58 + 34 * energy)),
        )
        dctx = DrummerRuntimeContext(
            position_in_bar_beats=beat,
            tempo_bpm=snapshot.transport.tempo_bpm,
            beats_per_bar=snapshot.transport.meter_numerator,
            phrase_position=phrase_position,
            ensemble_activity=snapshot.ensemble_density,
            soloist_activity=_soloist_activity(snapshot),
            energy_target=energy,
            section_transition=(
                snapshot.transport.form_position >= .96
                or directive.interaction.value == "transition"
            ),
            requested_kick="ensemble_kick" in directive.tags,
            harmonic_transition_confidence=float(context.get("harmonic_transition_confidence", 0.0)),
            harmony=context.get("harmonic_frame"),
        )
        chosen = perform_one_gesture(plan, dctx, self.memory)
        hits = tuple(
            RenderVoice(
                _DRUM_MIDI[h.voice],
                h.velocity,
                .10,
                _ms_to_beats(h.microtiming_ms, snapshot.transport.tempo_bpm),
                articulation=(h.articulation,),
                instrument_role="drums",
            )
            for h in chosen.gesture.hits
        )
        gesture = RenderGesture(
            role="drums",
            drum_hits=hits,
            source="player/drums:online_drummer",
            tags=tuple(sorted(chosen.gesture.tags | {chosen.gesture.role.value})),
            annotations={"drum_score": f"{chosen.score:.4f}"},
        )

        density = min(1.0, len(hits) / 4.0)
        return NativeImmediateResult(
            gesture=gesture,
            density=density,
            energy=energy,
            tension=float(context.get("ensemble_tension", snapshot.ensemble_tension)),
            leadership=.12 if chosen.gesture.role.value in {"setup", "accent"} else .03,
            phrase_maturity=0.0,
            tags=frozenset(set(chosen.gesture.tags) | {chosen.gesture.role.value}),
            provenance=("drummer_online_policy",),
        )


@dataclass
class PianoNativeDecider:
    state: PianoCompingState = PianoCompingState()
    evaluator: PianoCompingEvaluator = PianoCompingEvaluator()

    def __call__(self, context: Mapping[str, object]) -> NativeImmediateResult | None:
        request = context.get("piano_voicing_request")
        if request is None or not isinstance(request, PianoVoicingRequest):
            return None

        snapshot = context["ensemble_snapshot"]
        directive = context["interaction_directive"]
        phrase = _latest_other_phrase_maturity(snapshot, "piano")
        comping_context = PianoCompingContext(
            soloist_activity=_soloist_activity(snapshot),
            phrase_boundary_probability=phrase,
            available_space_beats=max(0.0, snapshot.space_available * 2.0),
            bass_activity=max((
                i.density for i in snapshot.intents if i.player_id == "bass"
            ), default=.5),
            drummer_activity=max((
                i.density for i in snapshot.intents if i.player_id == "drums"
            ), default=.5),
            ensemble_density=snapshot.ensemble_density,
            recent_piano_density=min(1.0, self.state.recent_density.voice_count / 6.0),
            section_energy=snapshot.ensemble_energy,
        )
        interaction_state = self.state.interaction_state_from_context(comping_context)
        slate = build_immediate_performance_candidates(
            request,
            comping_context,
            interaction_state,
            context.get("harmonic_affordance"),
            max_candidates=64,
        )
        musical_context = context.get("musical_context")
        if not isinstance(musical_context, MusicalContextVector):
            musical_context = MusicalContextVector(
                phrase_maturity=phrase,
                tension=snapshot.ensemble_tension,
                ensemble_activity=snapshot.ensemble_density,
            )
        plan = SoftPlan(
            horizon_beats=1.0,
            intention=directive.interaction.value,
            density_direction="down" if directive.density_delta < 0 else (
                "up" if directive.density_delta > 0 else "stable"
            ),
        )
        chosen = perform_one_comping_action(
            plan,
            self.evaluator,
            slate.candidates,
            comping_context,
            musical_context,
            self.state,
            harmonic_affordance=context.get("harmonic_affordance"),
            interaction_state=interaction_state,
            harmonic_frame=context.get("harmonic_frame"),
            harmonic_reasoning=context.get("harmonic_reasoning"),
        )

        candidate = chosen.candidate
        if candidate.realization is None:
            return NativeImmediateResult(
                gesture=None,
                density=0.0,
                energy=max(.1, snapshot.ensemble_energy * .35),
                tension=snapshot.ensemble_tension,
                leadership=.02,
                tags=frozenset({"piano_silence", candidate.role.value}),
                provenance=("piano_comping_policy",),
            )

        event = candidate.realization.event
        voices = tuple(
            RenderVoice(
                v.pitch_midi,
                event.velocity,
                event.duration_beats,
                event.onset_offset_beats + v.onset_offset_beats,
                articulation=event.articulation,
                instrument_role="piano",
            )
            for v in event.voices_by_onset
        )
        gesture = RenderGesture(
            role="piano",
            voices=voices,
            source="player/piano:comping_policy",
            tags=tuple(sorted(set(event.tags) | set(candidate.tags) | {candidate.role.value})),
            annotations={"piano_score": f"{chosen.total:.4f}"},
        )
        density = min(1.0, len(voices) / 6.0)
        return NativeImmediateResult(
            gesture=gesture,
            density=density,
            energy=max(.1, min(1.0, snapshot.ensemble_energy)),
            tension=snapshot.ensemble_tension,
            leadership=.08 if candidate.role.value in {"answer", "fill"} else .03,
            phrase_maturity=0.0,
            tags=frozenset(set(event.tags) | set(candidate.tags) | {candidate.role.value}),
            provenance=("piano_comping_policy",),
        )
