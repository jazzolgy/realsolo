from __future__ import annotations

from dataclasses import dataclass

from music_intelligence.harmony.jazz_harmony_core import (
    HarmonicEvidence,
    HarmonicFrame,
    HarmonySource,
    build_basic_affordances,
)
from music_intelligence.reasoning.legend_style_core import MusicalContextVector
from music_intelligence.reasoning.online_improviser import SoftPlan
from players.piano import (
    PianoCompingContext,
    PianoCompingEvaluator,
    PianoCompingState,
    PianoVoicingRequest,
    ResolvedHarmonicMaterial,
    build_immediate_performance_candidates,
    perform_one_comping_action,
)

from .player_adapter import committed_polyphonic_to_render_gesture
from .stage1_music import parse_chord


def _resolved_material(chord_symbol: str, affordance_id: str) -> ResolvedHarmonicMaterial:
    chord = parse_chord(chord_symbol)
    intervals = tuple(chord.intervals)
    roles: dict[str, tuple[int, ...]] = {"root": (chord.root_pc,)}

    role_by_interval = {
        3: "b3",
        4: "3rd",
        6: "b5",
        7: "5th",
        9: "6",
        10: "b7",
        11: "7th",
    }
    for interval in intervals[1:]:
        role = role_by_interval.get(interval % 12)
        if role:
            roles[role] = ((chord.root_pc + interval) % 12,)

    return ResolvedHarmonicMaterial(
        affordance_id=affordance_id,
        root_pitch_class=chord.root_pc,
        role_pitch_classes=roles,
    )


def _choose_affordance(chord_symbol: str, next_chord: str):
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
    frame = HarmonicFrame(
        expected=expected,
        next_expected=next_expected,
        phrase_position=0.5,
        tension=0.35,
    )
    affordances = build_basic_affordances(frame)
    specific = [a for a in affordances if not a.affordance_id.startswith("generic.")]
    return max(specific or affordances, key=lambda a: a.weight)


@dataclass
class Stage1PianoPlayer:
    """Bridge from chart expectation to the actual player/piano immediate policy."""

    state: PianoCompingState

    @classmethod
    def create(cls) -> "Stage1PianoPlayer":
        return cls(PianoCompingState())

    def reset(self) -> None:
        self.state = PianoCompingState()

    def decide(
        self,
        chord_symbol: str,
        next_chord: str,
        *,
        beat_in_bar: float,
        bar_index: int,
    ):
        affordance = _choose_affordance(chord_symbol, next_chord)
        material = _resolved_material(chord_symbol, affordance.affordance_id)

        boundary = 0.78 if beat_in_bar >= 3.0 else 0.22
        available = 1.0 if beat_in_bar >= 3.0 else 0.35
        context = PianoCompingContext(
            soloist_activity=0.48,
            phrase_boundary_probability=boundary,
            available_space_beats=available,
            bass_activity=0.55,
            drummer_activity=0.58,
            ensemble_density=0.46,
            recent_piano_density=min(1.0, self.state.recent_density.dynamic_weight),
            section_energy=0.48 + 0.08 * (bar_index % 4),
            time_feel="swing",
        )
        interaction = self.state.interaction_state_from_context(context)
        request = PianoVoicingRequest(
            material,
            bassist_present=True,
            low_midi=48,
            high_midi=82,
            duration_beats=0.65,
        )
        slate = build_immediate_performance_candidates(
            request,
            context,
            interaction,
            affordance,
            max_candidates=64,
        )
        plan = SoftPlan(
            horizon_beats=2.0,
            intention="support the soloist with one immediate piano gesture",
            soft_targets=("clarity", "space", "voice-leading"),
            candidate_families=("silence", "shell", "rootless", "response"),
        )
        musical_context = MusicalContextVector(
            chord_symbol=chord_symbol,
            metric_position=(beat_in_bar % 4.0) / 4.0,
            phrase_maturity=boundary,
            ensemble_activity=context.ensemble_density,
            next_harmony=next_chord,
        )
        chosen = perform_one_comping_action(
            plan,
            PianoCompingEvaluator(),
            slate.candidates,
            context,
            musical_context,
            self.state,
            affordance,
            interaction,
        )
        candidate = chosen.candidate
        if candidate.realization is None:
            return None

        return committed_polyphonic_to_render_gesture(
            candidate.realization.event,
            player_role="piano",
            source=candidate.realization.event.source_family,
            annotations={
                "comping_role": candidate.role.value,
                "comping_action": candidate.action_type.value,
            },
        )
