from __future__ import annotations

from dataclasses import dataclass

from music_intelligence.harmony.jazz_harmony_core import (
    HarmonicEvidence,
    HarmonicFrame,
    HarmonySource,
    build_basic_affordances,
)
from music_intelligence.reasoning.ensemble_state import (
    EnsembleState,
    PlayerPresence,
    PlayerRole,
    TransportState,
)
from music_intelligence.reasoning.legend_style_core import MusicalContextVector
from players.piano import PianoVoicingRequest

from .native_deciders import build_native_trio_runtime
from .stage1_music import parse_chord
from .stage1_piano import _resolved_material


def _chart_frame(chord_symbol: str, next_chord: str, *, phrase_position: float) -> HarmonicFrame:
    current = parse_chord(chord_symbol)
    expected = HarmonicEvidence(
        HarmonySource.EXPECTED,
        symbol=chord_symbol,
        root_pc=current.root_pc,
        pitch_classes=frozenset(current.pitch_classes),
        provenance=("stage1_chart",),
    )
    next_expected = None
    if next_chord:
        nxt = parse_chord(next_chord)
        next_expected = HarmonicEvidence(
            HarmonySource.EXPECTED,
            symbol=next_chord,
            root_pc=nxt.root_pc,
            pitch_classes=frozenset(nxt.pitch_classes),
            provenance=("stage1_chart",),
        )
    return HarmonicFrame(
        expected=expected,
        next_expected=next_expected,
        phrase_position=max(0.0, min(1.0, phrase_position)),
        tension=0.55 if "7" in chord_symbol and "maj7" not in chord_symbol else 0.28,
    )


def _affordance(frame: HarmonicFrame):
    choices = build_basic_affordances(frame)
    specific = [x for x in choices if not x.affordance_id.startswith("generic.")]
    return max(specific or choices, key=lambda x: x.weight)


@dataclass
class Stage1TrioRuntime:
    """Chart-driven Stage-1 shell around the real piano/bass/drums runtime."""

    loop: object
    state: EnsembleState

    @classmethod
    def create(cls, tempo_bpm: float = 120.0) -> "Stage1TrioRuntime":
        state = EnsembleState(
            transport=TransportState(
                beat=0.0,
                bar=0,
                section="A",
                chorus=0,
                tempo_bpm=tempo_bpm,
                meter_numerator=4,
                meter_denominator=4,
                form_position=0.0,
            ),
            players=(
                PlayerPresence("piano", "piano", PlayerRole.COMPER),
                PlayerPresence("bass", "upright_bass", PlayerRole.BASS),
                PlayerPresence("drums", "drum_kit", PlayerRole.DRUMS),
            ),
            ensemble_density=0.42,
            ensemble_energy=0.46,
            ensemble_tension=0.35,
            space_available=0.58,
        )
        return cls(build_native_trio_runtime(), state)

    def reset(self, tempo_bpm: float = 120.0) -> None:
        fresh = self.create(tempo_bpm)
        self.loop = fresh.loop
        self.state = fresh.state

    def decide(
        self,
        chord_symbol: str,
        next_chord: str,
        *,
        beat_in_bar: float,
        bar_index: int,
        total_bars: int,
        tempo_bpm: float,
        section: str = "",
        chorus: int = 0,
    ):
        form_position = 0.0 if total_bars <= 1 else bar_index / max(1, total_bars - 1)
        phrase_position = ((bar_index % 4) + beat_in_bar / 4.0) / 4.0
        frame = _chart_frame(
            chord_symbol,
            next_chord,
            phrase_position=phrase_position,
        )
        affordance = _affordance(frame)
        material = _resolved_material(chord_symbol, affordance.affordance_id)
        piano_request = PianoVoicingRequest(
            material,
            bassist_present=True,
            low_midi=48,
            high_midi=82,
            duration_beats=0.65,
        )

        self.state = EnsembleState(
            transport=TransportState(
                beat=beat_in_bar,
                bar=bar_index,
                section=section,
                chorus=chorus,
                tempo_bpm=tempo_bpm,
                meter_numerator=4,
                meter_denominator=4,
                form_position=max(0.0, min(1.0, form_position)),
            ),
            players=self.state.players,
            intents=self.state.intents,
            recent_interactions=self.state.recent_interactions,
            harmonic_state_id=chord_symbol,
            ensemble_density=self.state.ensemble_density,
            ensemble_energy=self.state.ensemble_energy,
            ensemble_tension=frame.tension,
            space_available=self.state.space_available,
            leader_player_id=self.state.leader_player_id,
            generation=self.state.generation + 1,
        )

        musical_context = MusicalContextVector(
            chord_symbol=chord_symbol,
            metric_position=(beat_in_bar % 4.0) / 4.0,
            phrase_maturity=phrase_position,
            tension=frame.tension,
            ensemble_activity=self.state.ensemble_density,
            next_harmony=next_chord,
        )
        result = self.loop.step(
            self.state,
            context={
                "harmonic_frame": frame,
                "harmonic_affordance": affordance,
                "piano_voicing_request": piano_request,
                "musical_context": musical_context,
                "ensemble_tension": frame.tension,
                "harmonic_transition_confidence": 0.9 if next_chord else 0.0,
            },
        )
        self.state = result.state
        return result
