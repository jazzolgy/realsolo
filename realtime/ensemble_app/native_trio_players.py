from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from players.bass import (
    BassContext,
    BassMode,
    BassSequentialRunner,
    BassStepInput,
    derive_bass_ensemble_signals,
)
from players.drums import (
    DrummerPerformanceMemory,
    DrummerRuntimeContext,
    DrummerSoftPlan,
    DrumVoice,
    TimeFeel,
    perform_one_gesture,
)
from music_intelligence.legends.scott_lafaro import SCOTT_LAFARO_PROFILE_VIEW
from music_intelligence.harmony import (
    HarmonicEvidence,
    HarmonicFrame,
    HarmonySource,
)

from .player_contract import RenderGesture, RenderVoice
from .stage1_music import parse_chord
from .stage1_piano import Stage1PianoPlayer
from .trio_adapters import NativeImmediateResult


_DRUM_MIDI = {
    DrumVoice.BASS_DRUM: 36,
    DrumVoice.SNARE: 38,
    DrumVoice.CLOSED_HIHAT: 42,
    DrumVoice.OPEN_HIHAT: 46,
    DrumVoice.RIDE: 51,
    DrumVoice.CRASH: 49,
    DrumVoice.HIGH_TOM: 50,
    DrumVoice.MID_TOM: 47,
    DrumVoice.FLOOR_TOM: 43,
    DrumVoice.COWBELL: 56,
    DrumVoice.CLAVE: 75,
}


def _frame(chord_symbol: str, next_chord: str = "") -> HarmonicFrame:
    chord = parse_chord(chord_symbol)
    expected = HarmonicEvidence(
        HarmonySource.EXPECTED,
        symbol=chord_symbol,
        root_pc=chord.root_pc,
        pitch_classes=frozenset(chord.pitch_classes),
        provenance=("realtime_chart",),
    )
    next_expected = None
    if next_chord:
        nxt = parse_chord(next_chord)
        next_expected = HarmonicEvidence(
            HarmonySource.EXPECTED,
            symbol=next_chord,
            root_pc=nxt.root_pc,
            pitch_classes=frozenset(nxt.pitch_classes),
            provenance=("realtime_chart",),
        )
    return HarmonicFrame(
        expected=expected,
        next_expected=next_expected,
        phrase_position=0.5,
        tension=0.35,
    )


@dataclass
class Stage1PianoNativeDecider:
    player: Stage1PianoPlayer = field(default_factory=Stage1PianoPlayer.create)

    def __call__(self, context: Mapping[str, object]) -> NativeImmediateResult | None:
        chord = str(context.get("chord_symbol", "Cmaj7"))
        next_chord = str(context.get("next_chord", ""))
        harmonic_frame = context.get("harmonic_frame")
        if harmonic_frame is None:
            harmonic_frame = _frame(chord, next_chord)
        beat = float(context.get("beat_in_bar", 0.0))
        bar = int(context.get("bar_index", 0))
        gesture = self.player.decide(
            chord,
            next_chord,
            beat_in_bar=beat,
            bar_index=bar,
        )
        directive = context["interaction_directive"]
        if gesture is None:
            return NativeImmediateResult(
                gesture=None,
                density=0.0,
                energy=0.25,
                tension=0.25,
                leadership=0.0,
                tags=frozenset({"piano_silence", directive.interaction.value}),
                provenance=("stage1_piano_native",),
            )
        voice_count = max(1, len(gesture.voices))
        return NativeImmediateResult(
            gesture=gesture,
            density=min(1.0, 0.18 + 0.16 * voice_count),
            energy=0.45,
            tension=0.35,
            leadership=0.08,
            tags=frozenset({"piano_comping", directive.interaction.value}),
            provenance=("stage1_piano_native",),
        )


@dataclass
class Stage1BassNativeDecider:
    """Realtime integration wrapper around the canonical Bass player."""

    runner: BassSequentialRunner = field(default_factory=BassSequentialRunner)

    def __call__(self, context: Mapping[str, object]) -> NativeImmediateResult | None:
        chord = str(context.get("chord_symbol", "Cmaj7"))
        next_chord = str(context.get("next_chord", ""))
        harmonic_frame = context.get("harmonic_frame")
        if harmonic_frame is None:
            harmonic_frame = _frame(chord, next_chord)
        beat = float(context.get("beat_in_bar", 0.0))
        meter = int(context.get("beats_per_bar", 4))
        tempo = float(context.get("tempo_bpm", 140.0))
        ensemble = context["ensemble_snapshot"]
        directive = context["interaction_directive"]

        signals = derive_bass_ensemble_signals(
            ensemble,
            bass_player_id="bass",
        )
        requested_mode = str(context.get("bass_mode", "walking")).lower()
        mode = BassMode.SOLO if requested_mode == "solo" else BassMode.WALKING
        requested_legend = str(context.get("bass_legend", "")).strip().lower()
        legend_profile = (
            SCOTT_LAFARO_PROFILE_VIEW
            if requested_legend in {"scott_lafaro", "lafaro"}
            else None
        )

        self.runner.tempo_bpm = tempo
        if bool(context.get("bass_ghost_only", False)):
            ghost=self.runner.ghost_step(
                beat_in_measure=beat % meter,
                absolute_beat=float(ensemble.transport.beat),
                mode=mode,
                ensemble_activity=signals.ensemble_activity,
                groove=ensemble.groove,
            )
            if not ghost.play:
                return NativeImmediateResult(
                    gesture=None,
                    density=0.0,
                    energy=.16,
                    tension=.20,
                    leadership=.0,
                    tags=frozenset({"bass_ghost_space","walking","eighth_offbeat"}),
                    provenance=("stage1_bass_native","player/bass:ghost_notes","space"),
                )
            gesture=RenderGesture(
                role="bass",
                voices=(RenderVoice(
                    pitch_midi=ghost.physical_pitch_midi,
                    velocity=ghost.velocity,
                    duration_beats=ghost.sounding_duration_beats,
                    onset_offset_beats=0.0,
                    articulation=(ghost.articulation.value,"ghost_note","eighth_offbeat"),
                    instrument_role="bass",
                ),),
                source="player/bass:walking_ghost",
                tags=("bass_ghost_note","walking","eighth_offbeat",ghost.articulation.value),
                annotations={
                    "ghost_score":f"{ghost.score:.4f}",
                    "rhythmic_value_beats":f"{ghost.rhythmic_value_beats:.3f}",
                },
            )
            return NativeImmediateResult(
                gesture=gesture,
                density=.14,
                energy=.24,
                tension=.22,
                leadership=.01,
                tags=frozenset({"bass_ghost_note","walking","eighth_offbeat",ghost.articulation.value}),
                provenance=("stage1_bass_native","player/bass:ghost_notes"),
            )

        musical_context = context.get("musical_context")
        own_phrase_progress = getattr(musical_context, "phrase_maturity", None)
        if own_phrase_progress is None and "phrase_position" in context:
            own_phrase_progress = float(context["phrase_position"])

        result = self.runner.step(BassStepInput(
            frame=harmonic_frame,
            mode=mode,
            beat_in_measure=beat % meter,
            absolute_beat=float(ensemble.transport.beat),
            phrase_boundary=bool(context.get("phrase_boundary", False)),
            form_boundary="form_boundary" in directive.tags,
            soloist_phrase_ending=signals.soloist_phrase_ending,
            drum_fill_active=signals.drum_fill_active,
            piano_fill_active=signals.piano_fill_active,
            low_register_conflict=signals.low_register_conflict,
            ensemble_activity=signals.ensemble_activity,
            phrase_progress=(
                own_phrase_progress
                if mode is BassMode.SOLO
                else signals.phrase_progress
            ),
            directive=directive,
            legend_profile=legend_profile,
        ))

        event = result.candidate.event
        if event.pitch_midi is None:
            return NativeImmediateResult(
                gesture=None,
                density=0.0,
                energy=max(.18, result.phrase_intent.articulation_energy * .55),
                tension=.42,
                leadership=.68 if mode is BassMode.SOLO else .04,
                phrase_maturity=float(own_phrase_progress or 0.0),
                tags=frozenset({
                    "bass_space",
                    mode.value,
                    result.phrase_intent.kind.value,
                    result.solo_plan.operation.value if result.solo_plan else "none",
                }),
                provenance=(
                    "stage1_bass_native",
                    "player/bass:sequential_runner",
                    "active_space_event",
                    *signals.provenance,
                ),
            )
        rendered = result.render_event
        assert rendered is not None

        gesture = RenderGesture(
            role="bass",
            voices=(RenderVoice(
                pitch_midi=rendered.pitch_midi,
                velocity=rendered.velocity,
                duration_beats=rendered.duration_beats,
                onset_offset_beats=rendered.onset_offset_beats,
                articulation=rendered.articulation,
                instrument_role=rendered.instrument_role,
            ),),
            source="player/bass:sequential_runner",
            tags=tuple(sorted(
                event.tags
                | frozenset({
                    result.candidate.harmonic_role.value,
                    result.phrase_intent.kind.value,
                    result.interaction.intent.value,
                })
            )),
            annotations={
                "harmonic_role": result.candidate.harmonic_role.value,
                "phrase_intent": result.phrase_intent.kind.value,
                "interaction_intent": result.interaction.intent.value,
                "bass_mode": mode.value,
                "solo_operation": (
                    result.solo_plan.operation.value
                    if result.solo_plan is not None else ""
                ),
                "solo_family": (
                    result.solo_plan.family.value
                    if result.solo_plan is not None else ""
                ),
                "legend_id": (
                    legend_profile.legend_id
                    if legend_profile is not None else ""
                ),
            },
        )

        stable = result.candidate.harmonic_role.value in {
            "root", "fifth", "chord_tone", "pedal"
        }
        density = max(
            .12,
            min(
                .78,
                result.phrase_intent.information_density_target
                + .35 * result.interaction.density_delta,
            ),
        )
        energy = max(
            .18,
            min(
                .88,
                .32
                + .34 * result.candidate.expression.accent
                + .20 * result.phrase_intent.articulation_energy,
            ),
        )
        return NativeImmediateResult(
            gesture=gesture,
            density=density,
            energy=energy,
            tension=.34 if stable else .57,
            leadership=.68 if mode is BassMode.SOLO else .04,
            phrase_maturity=float(own_phrase_progress or 0.0),
            tags=frozenset({
                "bass_sequential",
                mode.value,
                directive.interaction.value,
                result.phrase_intent.kind.value,
                result.solo_plan.operation.value if result.solo_plan else "none",
                legend_profile.legend_id if legend_profile is not None else "generic",
            }),
            provenance=(
                "stage1_bass_native",
                "player/bass:sequential_runner",
                *signals.provenance,
            ),
        )


@dataclass
class Stage1DrumsNativeDecider:
    memory: DrummerPerformanceMemory = field(default_factory=DrummerPerformanceMemory)

    def __call__(self, context: Mapping[str, object]) -> NativeImmediateResult | None:
        beat = float(context.get("beat_in_bar", 0.0))
        tempo = float(context.get("tempo_bpm", 140.0))
        meter = int(context.get("beats_per_bar", 4))
        phrase = float(context.get("phrase_position", .5))
        ensemble = context["ensemble_snapshot"]
        directive = context["interaction_directive"]

        energy = max(.15, min(.9, ensemble.ensemble_energy + directive.energy_delta))
        density = max(.08, min(.82, .30 + directive.density_delta))
        plan = DrummerSoftPlan(
            feel=(TimeFeel.SWING if ensemble.groove is None or ensemble.groove.feel.value in {"swing","shuffle"} else TimeFeel.STRAIGHT),
            energy=energy,
            comping_density=density,
            interaction_intent=directive.interaction.value,
        )
        runtime = DrummerRuntimeContext(
            position_in_bar_beats=beat % meter,
            tempo_bpm=tempo,
            beats_per_bar=meter,
            phrase_position=phrase,
            ensemble_activity=ensemble.ensemble_density,
            soloist_activity=max(
                (i.density for i in ensemble.intents if i.player_id not in {"drums","bass","piano"}),
                default=.45,
            ),
            energy_target=energy,
            section_transition="form_boundary" in directive.tags,
            requested_kick="explicit_kick" in directive.tags,
            harmonic_transition_confidence=.75 if "form_boundary" in directive.tags else .25,
            harmony=context.get("harmonic_frame"),
            groove=ensemble.groove,
        )
        chosen = perform_one_gesture(plan, runtime, self.memory)
        g = chosen.gesture
        hits = []
        for hit in g.hits:
            midi = _DRUM_MIDI.get(hit.voice)
            if midi is None:
                continue
            hits.append(RenderVoice(
                pitch_midi=midi,
                velocity=hit.velocity,
                duration_beats=.12,
                onset_offset_beats=(hit.microtiming_ms / 1000.0) * tempo / 60.0 + getattr(hit, "onset_offset_beats", 0.0),
                articulation=(hit.articulation,),
                instrument_role="drums",
            ))
        gesture = RenderGesture(
            role="drums",
            drum_hits=tuple(hits),
            source="player/drums:online_drummer",
            tags=tuple(sorted(g.tags | frozenset({g.role.value}))),
            annotations={"gesture_role": g.role.value},
        )
        return NativeImmediateResult(
            gesture=gesture,
            density=min(1.0, len(hits) / 4.0),
            energy=energy,
            tension=min(1.0, .25 + .12 * len(hits)),
            leadership=.05 if g.role.value in {"time","comp"} else .18,
            phrase_maturity=phrase,
            tags=frozenset({"drum_immediate", directive.interaction.value, g.role.value}),
            provenance=("stage1_drums_native",),
        )
