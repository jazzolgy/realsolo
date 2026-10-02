from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from players.bass import (
    BassContext,
    BassMode,
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
    previous_pitch: int | None = None
    previous_interval: int | None = None

    def __call__(self, context: Mapping[str, object]) -> NativeImmediateResult | None:
        chord = str(context.get("chord_symbol", "Cmaj7"))
        next_chord = str(context.get("next_chord", ""))
        beat = float(context.get("beat_in_bar", 0.0))
        meter = int(context.get("beats_per_bar", 4))
        ensemble = context["ensemble_snapshot"]
        directive = context["interaction_directive"]

        bass_context = BassContext(
            mode=BassMode.WALKING,
            beat_in_measure=beat % meter,
            meter_numerator=meter,
            previous_pitch_midi=self.previous_pitch,
            previous_motion_semitones=self.previous_interval,
            ensemble_activity=ensemble.ensemble_density,
        )
        chosen = choose_immediate_bass_action(_frame(chord, next_chord), bass_context)
        event = chosen.event
        if event.pitch_midi is None:
            return None

        pitch = event.pitch_midi
        if self.previous_pitch is not None:
            self.previous_interval = pitch - self.previous_pitch
        self.previous_pitch = pitch

        expr = chosen.expression
        velocity = int(round(38 + 70 * expr.accent))
        duration = max(.12, event.duration_beats * expr.sounding_length_ratio)
        gesture = RenderGesture(
            role="bass",
            voices=(RenderVoice(
                pitch_midi=pitch,
                velocity=max(1, min(127, velocity)),
                duration_beats=duration,
                onset_offset_beats=expr.microtiming_ms / 1000.0,
                articulation=(expr.articulation.value,),
                instrument_role="bass",
            ),),
            source="player/bass:immediate_realizer",
            tags=tuple(sorted(event.tags | frozenset({chosen.harmonic_role.value}))),
            annotations={"harmonic_role": chosen.harmonic_role.value},
        )
        return NativeImmediateResult(
            gesture=gesture,
            density=0.42,
            energy=max(.2, min(.85, .42 + .25 * expr.accent)),
            tension=.35 if chosen.harmonic_role.value in {"root","fifth","chord_tone","pedal"} else .58,
            leadership=.04,
            tags=frozenset({"bass_immediate", directive.interaction.value}),
            provenance=("stage1_bass_native",),
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
            feel=TimeFeel.SWING,
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
                onset_offset_beats=hit.microtiming_ms / 1000.0,
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
