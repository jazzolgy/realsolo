from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from players.bass import (
    BassCommittedAction,
    BassContext,
    BassInteractionContext,
    BassMode,
    BassPerformanceMemory,
    choose_bass_interaction_intent,
    choose_immediate_bass_action,
)
from players.drums import (
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
from .native_trio_players import Stage1BassNativeDecider
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
    """Compatibility facade over the canonical sequential Bass player.

    Realtime must not own a second bass musical policy.  The legacy class name
    remains for callers/tests, while all decisions delegate to the canonical
    Stage1BassNativeDecider / players.bass.BassSequentialRunner path.
    """

    mode: BassMode = BassMode.WALKING
    delegate: Stage1BassNativeDecider = field(default_factory=Stage1BassNativeDecider)

    @property
    def memory(self):
        return self.delegate.runner.memory

    def __call__(self, context: Mapping[str, object]) -> NativeImmediateResult | None:
        forwarded = dict(context)
        forwarded.setdefault("bass_mode", self.mode.value)
        return self.delegate(forwarded)


@dataclass
class DrumsNativeDecider:
    memory: DrummerPerformanceMemory = field(default_factory=DrummerPerformanceMemory)
    feel: TimeFeel = TimeFeel.SWING

    def __call__(self, context: Mapping[str, object]) -> NativeImmediateResult | None:
        snapshot = context["ensemble_snapshot"]
        directive = context["interaction_directive"]
        beat = float(snapshot.transport.beat) % snapshot.transport.meter_numerator
        phrase_position = _latest_other_phrase_maturity(snapshot, "drums")
        energy = max(0.0, min(1.0, snapshot.ensemble_energy + directive.energy_delta))

        shared_feel = snapshot.groove.feel.value if snapshot.groove is not None else self.feel.value
        drum_feel = TimeFeel.SWING if shared_feel in {"swing","shuffle"} else TimeFeel.STRAIGHT
        plan = DrummerSoftPlan(
            feel=drum_feel,
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
            groove=snapshot.groove,
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
    state: PianoCompingState = field(default_factory=PianoCompingState)
    evaluator: PianoCompingEvaluator = field(default_factory=PianoCompingEvaluator)

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
            time_feel=(snapshot.groove.feel.value if snapshot.groove is not None else "swing"),
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

def build_native_trio_runtime():
    """Construct the current executable piano/bass/drums runtime loop."""
    from .runtime_loop import EnsembleRuntimeLoop
    from .trio_adapters import PianoRuntimeAdapter, BassRuntimeAdapter, DrumsRuntimeAdapter

    return EnsembleRuntimeLoop((
        PianoRuntimeAdapter(PianoNativeDecider()),
        BassRuntimeAdapter(BassNativeDecider()),
        DrumsRuntimeAdapter(DrumsNativeDecider()),
    ))
