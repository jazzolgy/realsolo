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
from music_intelligence.reasoning.groove_context import (
    EnsembleTempoState,
    GrooveCoordinationMode,
    GrooveFeel,
    build_groove_context,
    evolve_ensemble_tempo,
)
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
    tempo_state: EnsembleTempoState

    @classmethod
    def create(
        cls,
        tempo_bpm: float = 120.0,
        groove_feel: GrooveFeel = GrooveFeel.SWING,
        coordination_mode: GrooveCoordinationMode = GrooveCoordinationMode.ELASTIC,
    ) -> "Stage1TrioRuntime":
        groove = build_groove_context(
            groove_feel,
            tempo_bpm=tempo_bpm,
            meter_numerator=4,
            meter_denominator=4,
            grammar_id=(
                "swing.eighth_triplet_feel"
                if groove_feel is GrooveFeel.SWING
                else groove_feel.value
            ),
            subdivision_hint=(
                "swing_eighth"
                if groove_feel is GrooveFeel.SWING
                else "style_specific"
            ),
            coordination_mode=coordination_mode,
            phase_elasticity=0.0 if coordination_mode is GrooveCoordinationMode.LOCKED else 0.72,
            swing_elasticity=0.0 if coordination_mode is GrooveCoordinationMode.LOCKED else 0.60,
            tempo_elasticity=0.85 if coordination_mode is GrooveCoordinationMode.HUMAN_DRIFT else 0.0,
            provenance=("stage1_preperformance_init",),
        )
        state = EnsembleState(
            transport=TransportState(
                beat=0.0,
                bar=0,
                section="A",
                chorus=0,
                tempo_bpm=groove.tempo_bpm,
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
            groove=groove,
        )
        return cls(
            build_native_trio_runtime(),
            state,
            EnsembleTempoState(tempo_bpm,tempo_bpm,tempo_bpm),
        )

    def reset(self, tempo_bpm: float = 120.0) -> None:
        mode=(self.state.groove.coordination_mode if self.state.groove is not None else GrooveCoordinationMode.ELASTIC)
        fresh = self.create(tempo_bpm, coordination_mode=mode)
        self.loop = fresh.loop
        self.state = fresh.state
        self.tempo_state = fresh.tempo_state

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
        bass_solo: bool = False,
        bass_legend: str = "",
        active_player_ids: frozenset[str] | None = None,
        bass_ghost_only: bool = False,
        coordination_mode: GrooveCoordinationMode | None = None,
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

        active_players = tuple(
            PlayerPresence(
                p.player_id,
                p.instrument,
                (
                    PlayerRole.SOLOIST
                    if bass_solo and p.player_id == "bass"
                    else PlayerRole.BASS
                    if not bass_solo and p.player_id == "bass"
                    else p.role
                ),
                (
                    p.player_id in active_player_ids
                    if active_player_ids is not None
                    else True
                ),
            )
            for p in self.state.players
        )

        mode=(
            coordination_mode
            if coordination_mode is not None
            else self.state.groove.coordination_mode
            if self.state.groove is not None
            else GrooveCoordinationMode.ELASTIC
        )
        if self.tempo_state.reference_tempo_bpm != tempo_bpm:
            self.tempo_state=EnsembleTempoState(tempo_bpm,tempo_bpm,tempo_bpm)

        prior_intents=self.state.intents
        if prior_intents:
            weighted=sum(
                (intent.energy-.5) * (.35+.65*intent.leadership)
                for intent in prior_intents
            )/len(prior_intents)
        else:
            weighted=0.0
        phrase_release=max(0.0,min(1.0,(phrase_position-.72)/.28))

        groove = build_groove_context(
            self.state.groove.feel if self.state.groove is not None else GrooveFeel.SWING,
            tempo_bpm=self.tempo_state.current_tempo_bpm,
            meter_numerator=4,
            meter_denominator=4,
            grammar_id=(
                self.state.groove.grammar_id
                if self.state.groove is not None
                else "swing.eighth_triplet_feel"
            ),
            subdivision_hint=(
                self.state.groove.subdivision_hint
                if self.state.groove is not None
                else "swing_eighth"
            ),
            coordination_mode=mode,
            phase_elasticity=0.0 if mode is GrooveCoordinationMode.LOCKED else 0.72,
            swing_elasticity=0.0 if mode is GrooveCoordinationMode.LOCKED else 0.60,
            tempo_elasticity=0.85 if mode is GrooveCoordinationMode.HUMAN_DRIFT else 0.0,
            provenance=("stage1_preperformance_init","tempo_refresh"),
        )
        self.tempo_state=evolve_ensemble_tempo(
            self.tempo_state,
            groove,
            collective_push=weighted,
            phrase_release=phrase_release,
        )
        if mode is GrooveCoordinationMode.HUMAN_DRIFT:
            groove = build_groove_context(
                groove.feel,
                tempo_bpm=self.tempo_state.current_tempo_bpm,
                meter_numerator=groove.meter_numerator,
                meter_denominator=groove.meter_denominator,
                groove_strength=groove.groove_strength,
                swing_ratio=groove.swing_ratio,
                grammar_id=groove.grammar_id,
                subdivision_hint=groove.subdivision_hint,
                confidence=groove.confidence,
                coordination_mode=mode,
                phase_elasticity=groove.phase_elasticity,
                swing_elasticity=groove.swing_elasticity,
                tempo_elasticity=groove.tempo_elasticity,
                provenance=groove.provenance+("human_drift_update",),
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
            players=active_players,
            intents=self.state.intents,
            recent_interactions=self.state.recent_interactions,
            harmonic_state_id=chord_symbol,
            ensemble_density=self.state.ensemble_density,
            ensemble_energy=self.state.ensemble_energy,
            ensemble_tension=frame.tension,
            space_available=self.state.space_available,
            leader_player_id=self.state.leader_player_id,
            groove=groove,
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
                "phrase_position": phrase_position,
                "bass_mode": "solo" if bass_solo else "walking",
                "bass_legend": bass_legend,
                "groove_context": groove,
                "time_feel": groove.feel.value,
                "groove_coordination_mode": groove.coordination_mode.value,
                "effective_tempo_bpm": groove.tempo_bpm,
                "bass_ghost_only": bass_ghost_only,
            },
        )
        self.state = result.state
        return result
