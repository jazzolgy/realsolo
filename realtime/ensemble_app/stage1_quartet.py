from __future__ import annotations

from dataclasses import dataclass

from music_intelligence.reasoning.ensemble_state import (
    EnsembleState,
    PlayerPresence,
    PlayerRole,
    TransportState,
)
from music_intelligence.reasoning.legend_style_core import MusicalContextVector
from music_intelligence.reasoning.performance_convention import (
    default_performance_convention,
)
from music_intelligence.reasoning.groove_context import (
    GrooveCoordinationMode,
    GrooveFeel,
    build_groove_context,
)
from players.piano import PianoVoicingRequest

from .native_deciders import build_native_quartet_runtime
from .stage1_piano import _resolved_material
from .stage1_trio import _affordance, _chart_frame
from .stage1_music import parse_chord
from music_intelligence.corpus import ScoreContextSnapshot, ScorePosition


@dataclass
class Stage1QuartetRuntime:
    """Chart-driven canonical Piano/Bass/Drums/Tenor-Sax runtime shell.

    All four providers read the same immutable EnsembleState snapshot for a
    tick. Publication remains owned by EnsembleRuntimeLoop and happens only
    after all immediate decisions have been made.
    """

    loop: object
    state: EnsembleState

    @classmethod
    def create(
        cls,
        tempo_bpm: float = 172.0,
        groove_feel: GrooveFeel = GrooveFeel.SWING,
    ) -> "Stage1QuartetRuntime":
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
            coordination_mode=GrooveCoordinationMode.ELASTIC,
            tempo_elasticity=0.0,
            provenance=("stage1_quartet_preperformance_init",),
        )
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
                PlayerPresence("sax", "tenor_sax", PlayerRole.SOLOIST),
            ),
            ensemble_density=0.42,
            ensemble_energy=0.46,
            ensemble_tension=0.35,
            space_available=0.58,
            leader_player_id="sax",
            groove=groove,
        )
        return cls(build_native_quartet_runtime(), state)

    def reset(self, tempo_bpm: float = 172.0) -> None:
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
        active_player_ids: frozenset[str] | None = None,
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

        players = tuple(
            PlayerPresence(
                p.player_id,
                p.instrument,
                p.role,
                p.player_id in active_player_ids if active_player_ids is not None else True,
            )
            for p in self.state.players
        )

        old_groove = self.state.groove
        groove = build_groove_context(
            old_groove.feel if old_groove is not None else GrooveFeel.SWING,
            tempo_bpm=tempo_bpm,
            meter_numerator=4,
            meter_denominator=4,
            grammar_id=(
                old_groove.grammar_id if old_groove is not None
                else "swing.eighth_triplet_feel"
            ),
            subdivision_hint=(
                old_groove.subdivision_hint if old_groove is not None
                else "swing_eighth"
            ),
            coordination_mode=(
                old_groove.coordination_mode
                if old_groove is not None
                else GrooveCoordinationMode.ELASTIC
            ),
            phase_elasticity=(
                old_groove.phase_elasticity if old_groove is not None else .55
            ),
            swing_elasticity=(
                old_groove.swing_elasticity if old_groove is not None else .35
            ),
            tempo_elasticity=0.0,
            provenance=("stage1_quartet_preperformance_init","tempo_refresh"),
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
            players=players,
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

        next_parsed=parse_chord(next_chord) if next_chord else None
        sax_targets=frozenset(
            pc for idx,pc in enumerate(next_parsed.pitch_classes)
            if idx in {1,3}
        ) if next_parsed is not None else frozenset()
        # Autumn Leaves G minor and its relative Bb-major region share this
        # seven-note collection; this is harmonic/form context, not head melody.
        sax_local_key=frozenset({7,9,10,0,2,3,5})
        sax_score_snapshot=ScoreContextSnapshot(
            book_id="canonical_repertoire",
            song_id="autumn_leaves_g_minor_jam",
            position=ScorePosition(
                page=1,
                bar=bar_index+1,
                beat=beat_in_bar,
            ),
            style=("jazz","bebop"),
            meter="4/4",
            section=section or None,
            current_feel="swing",
            solo_indication="open_solo",
            confidence=1.0,
            provenance=("canonical_repertoire:autumn_leaves_harmony_form",),
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
                "chord_symbol": chord_symbol,
                "next_chord": next_chord,
                "beat_in_bar": beat_in_bar,
                "bar_index": bar_index,
                "tempo_bpm": tempo_bpm,
                "beats_per_bar": 4,
                "piano_voicing_request": piano_request,
                "musical_context": musical_context,
                "ensemble_tension": frame.tension,
                "harmonic_transition_confidence": 0.9 if next_chord else 0.0,
                "phrase_position": phrase_position,
                "bass_mode": "walking",
                "groove_context": groove,
                "time_feel": groove.feel.value,
                "sax_allow_improvisation": True,
                "sax_score_snapshot": sax_score_snapshot,
                "sax_target_pitch_classes": sax_targets,
                "sax_local_key_pitch_classes": sax_local_key,
                "decision_step_beats": .5,
                "song_id": "autumn_leaves_g_minor_jam",
                "performance_convention": default_performance_convention("jazz"),
            },
        )
        self.state = result.state
        return result
