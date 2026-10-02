"""Online drum-solo intelligence.

A drum solo is not modeled as an elongated fill.  The engine develops rhythmic
ideas over time while preserving form awareness and one-gesture-at-a-time
runtime commitment.

Source-derived concepts currently encoded:
- Riley, The Art of Bop Drumming: one-bar idea -> repetition -> orchestration ->
  adding rests -> rests within phrase -> rhythmic elasticity; three-beat phrases.
- Riley, Beyond Bop Drumming: three-beat phrases with rests, triplets in groups
  of four, variations, and longer modern-jazz phrase organization.
- Atkinson/Colaiuta, The UnReel Drum Book: asymmetric 5-5-5-6 groupings and
  systematic displacement / subdivision breakdown practice.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from music_intelligence.reasoning.solo_grammar import (
    SoloArc as SharedSoloArc,
    SoloDevelopmentOperation,
    SoloMethodContext,
    shared_solo_method_options,
)

from .legend_adapter import (
    DrumLegendProjection,
    DrumVocabularyIntent,
    legend_gesture_adjustment,
    vocabulary_gesture_adjustment,
)
from .model import (
    DrumGesture,
    DrumHit,
    DrummerRuntimeContext,
    DrumVoice,
    GestureRole,
    Limb,
)


class SoloDevelopment(str, Enum):
    STATE = "state"
    REPEAT = "repeat"
    ORCHESTRATE = "orchestrate"
    ADD_SPACE = "add_space"
    INTERNAL_REST = "internal_rest"
    ELASTICITY_EXPAND = "elasticity_expand"
    ELASTICITY_CONTRACT = "elasticity_contract"
    DISPLACE = "displace"
    THREE_BEAT_CYCLE = "three_beat_cycle"
    METRIC_ILLUSION = "metric_illusion"
    CONTRAST = "contrast"
    RECAP = "recap"
    RESOLVE = "resolve"


class SoloArc(str, Enum):
    OPEN = "open"
    DEVELOP = "develop"
    INTENSIFY = "intensify"
    CLIMAX = "climax"
    RELEASE = "release"
    REENTRY = "reentry"


_SHARED_DEVELOPMENT_MAP = {
    SoloDevelopment.STATE: SoloDevelopmentOperation.STATE,
    SoloDevelopment.REPEAT: SoloDevelopmentOperation.REPEAT,
    SoloDevelopment.ORCHESTRATE: SoloDevelopmentOperation.REORCHESTRATE,
    SoloDevelopment.ADD_SPACE: SoloDevelopmentOperation.ADD_SPACE,
    SoloDevelopment.INTERNAL_REST: SoloDevelopmentOperation.INTERNAL_REST,
    SoloDevelopment.ELASTICITY_EXPAND: SoloDevelopmentOperation.EXTEND,
    SoloDevelopment.ELASTICITY_CONTRACT: SoloDevelopmentOperation.CONTRACT,
    SoloDevelopment.DISPLACE: SoloDevelopmentOperation.DISPLACE,
    SoloDevelopment.THREE_BEAT_CYCLE: SoloDevelopmentOperation.DISPLACE,
    SoloDevelopment.METRIC_ILLUSION: SoloDevelopmentOperation.DISPLACE,
    SoloDevelopment.CONTRAST: SoloDevelopmentOperation.CONTRAST,
    SoloDevelopment.RECAP: SoloDevelopmentOperation.RECAP,
    SoloDevelopment.RESOLVE: SoloDevelopmentOperation.RESOLVE,
}


def shared_operation_for_drum_development(
    development: SoloDevelopment,
) -> SoloDevelopmentOperation:
    return _SHARED_DEVELOPMENT_MAP[development]


def _shared_method_bonus(
    plan: "DrumSoloPlan",
    context: DrummerRuntimeContext,
    state: "DrumSoloState",
    development: SoloDevelopment,
) -> tuple[float, tuple[str, ...]]:
    shared_context = SoloMethodContext(
        phrase_maturity=max(0.0, min(1.0, context.phrase_position)),
        tension=max(0.0, min(1.0, plan.intensity)),
        ensemble_activity=max(0.0, min(1.0, context.ensemble_activity)),
        recent_repetition_count=state.motif_repetitions,
        phrase_space_available=max(0.0, min(1.0, plan.space_probability)),
        form_boundary_pressure=1.0 if context.section_transition else 0.0,
        future_harmony_available=False,
        interaction_role="",
    )
    shared_arc = SharedSoloArc(plan.arc.value)
    desired = shared_operation_for_drum_development(development)
    matches = [
        option for option in shared_solo_method_options(shared_context, arc=shared_arc)
        if option.operation is desired
    ]
    if not matches:
        return 0.0, ()
    best = max(matches, key=lambda option: option.weight)
    return 0.25 * best.weight, best.reasons


@dataclass(frozen=True)
class SoloVocabularyCell:
    cell_id: str
    source_id: str
    source_page: str
    grouping: tuple[int, ...]
    subdivision: str
    length_beats: float
    tags: frozenset[str]
    exact_structural_pattern: bool
    notes: str = ""

    def validate(self) -> None:
        if not self.grouping or any(x <= 0 for x in self.grouping):
            raise ValueError("solo grouping must contain positive units")
        if self.length_beats <= 0:
            raise ValueError("solo cell length must be positive")


SOLO_VOCABULARY: tuple[SoloVocabularyCell, ...] = (
    SoloVocabularyCell(
        "riley_one_bar_development",
        "riley_art_bop",
        "pp. 36-39 in uploaded PDF",
        (1,),
        "phrase",
        4.0,
        frozenset({"jazz", "bop", "one_bar", "motif_development"}),
        False,
        "Source teaches development of a one-bar idea by repetition, orchestration, rests and rhythmic elasticity.",
    ),
    SoloVocabularyCell(
        "riley_three_beat_cycle",
        "riley_art_bop",
        "pp. 40-42 in uploaded PDF",
        (3,),
        "beat_cycle",
        3.0,
        frozenset({"jazz", "bop", "three_beat_phrase", "displacement"}),
        True,
        "Three-beat phrase cell intended to cycle across 4/4 and create displacement.",
    ),
    SoloVocabularyCell(
        "beyond_bop_triplets_groups_of_four",
        "riley_beyond_bop",
        "p. 47 in uploaded PDF",
        (4,),
        "triplet_stream",
        4.0 / 3.0,
        frozenset({"jazz", "post_bop", "triplet", "group_of_four", "metric_illusion"}),
        True,
        "Four-note grouping imposed on a triplet stream, producing a shifting pulse illusion.",
    ),
    SoloVocabularyCell(
        "unreel_america_5_5_5_6",
        "atkinson_unreel",
        "pp. 120-123 in uploaded PDF",
        (5, 5, 5, 6),
        "sixteenth",
        21.0 / 4.0,
        frozenset({"fusion", "advanced", "asymmetric", "quintuplet_related", "displacement"}),
        True,
        "America solo breakdown explicitly describes the fill as phrased 5, 5, 5, 6 and practices shifting it over sixteenths.",
    ),
)


@dataclass(frozen=True)
class DrumSoloPlan:
    arc: SoloArc = SoloArc.OPEN
    development: SoloDevelopment = SoloDevelopment.STATE
    motif_cell_id: str = "riley_one_bar_development"
    intensity: float = 0.45
    density: float = 0.45
    space_probability: float = 0.18
    preserve_form: bool = True
    target_reentry: bool = False
    adventurousness: float = 0.35

    def validate(self) -> None:
        for name in ("intensity", "density", "space_probability", "adventurousness"):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be within 0..1")
        solo_cell(self.motif_cell_id)


@dataclass
class DrumSoloState:
    gestures_committed: int = 0
    statements: int = 0
    spaces: int = 0
    last_voice: DrumVoice | None = None
    last_development: SoloDevelopment | None = None
    motif_repetitions: int = 0

    def observe(self, gesture: DrumGesture, development: SoloDevelopment) -> None:
        self.gestures_committed += 1
        self.last_development = development
        if gesture.role is GestureRole.SPACE:
            self.spaces += 1
        else:
            self.statements += 1
            if gesture.hits:
                self.last_voice = gesture.hits[-1].voice
        if development is SoloDevelopment.REPEAT:
            self.motif_repetitions += 1
        elif development not in {SoloDevelopment.STATE, SoloDevelopment.RECAP}:
            self.motif_repetitions = 0


@dataclass(frozen=True)
class SoloCandidate:
    gesture: DrumGesture
    development: SoloDevelopment
    score: float
    reasons: tuple[tuple[str, float], ...] = ()


def solo_cell(cell_id: str) -> SoloVocabularyCell:
    for cell in SOLO_VOCABULARY:
        if cell.cell_id == cell_id:
            cell.validate()
            return cell
    raise KeyError(cell_id)


def _voice_for_orchestration(index: int, intensity: float) -> DrumVoice:
    palette = (
        DrumVoice.SNARE,
        DrumVoice.HIGH_TOM,
        DrumVoice.MID_TOM,
        DrumVoice.FLOOR_TOM,
        DrumVoice.RIDE,
    )
    if intensity > 0.82:
        palette = palette + (DrumVoice.CRASH,)
    return palette[index % len(palette)]


def _limb_for_voice(voice: DrumVoice, index: int) -> Limb:
    if voice is DrumVoice.BASS_DRUM:
        return Limb.RIGHT_FOOT
    if voice in {DrumVoice.RIDE, DrumVoice.CRASH}:
        return Limb.RIGHT_HAND
    return Limb.RIGHT_HAND if index % 2 == 0 else Limb.LEFT_HAND


def _statement_gesture(
    plan: DrumSoloPlan,
    state: DrumSoloState,
    development: SoloDevelopment,
) -> DrumGesture:
    """Create one immediate solo statement gesture, never a future phrase."""
    voice_index = state.gestures_committed
    if development is SoloDevelopment.ORCHESTRATE:
        voice_index += state.statements
    elif development is SoloDevelopment.CONTRAST:
        voice_index += 2
    elif development in {SoloDevelopment.RECAP, SoloDevelopment.RESOLVE}:
        voice_index += 3

    voice = _voice_for_orchestration(voice_index, plan.intensity)
    velocity = int(52 + 62 * plan.intensity)
    articulation = {
        SoloDevelopment.REPEAT: "motif",
        SoloDevelopment.ORCHESTRATE: "orchestrated_motif",
        SoloDevelopment.DISPLACE: "displaced",
        SoloDevelopment.THREE_BEAT_CYCLE: "three_beat_cycle",
        SoloDevelopment.METRIC_ILLUSION: "metric_illusion",
        SoloDevelopment.RECAP: "recap",
        SoloDevelopment.RESOLVE: "resolution",
    }.get(development, "solo")

    gesture = DrumGesture(
        hits=(
            DrumHit(
                voice=voice,
                limb=_limb_for_voice(voice, voice_index),
                velocity=max(1, min(127, velocity)),
                articulation=articulation,
            ),
        ),
        role=GestureRole.FILL,
        tags=frozenset({
            "drum_solo",
            plan.arc.value,
            development.value,
            plan.motif_cell_id,
        }),
        confidence=0.9,
        provenance=("drum_player", "solo_engine", plan.motif_cell_id),
    )
    gesture.validate()
    return gesture


def _development_options(
    plan: DrumSoloPlan,
    context: DrummerRuntimeContext,
    state: DrumSoloState,
) -> tuple[SoloDevelopment, ...]:
    options: list[SoloDevelopment] = [
        SoloDevelopment.STATE,
        SoloDevelopment.REPEAT,
        SoloDevelopment.ORCHESTRATE,
        SoloDevelopment.ADD_SPACE,
        SoloDevelopment.INTERNAL_REST,
    ]

    if state.statements >= 2:
        options += [SoloDevelopment.DISPLACE, SoloDevelopment.CONTRAST]
    if plan.adventurousness >= 0.4:
        options += [SoloDevelopment.THREE_BEAT_CYCLE]
    if plan.adventurousness >= 0.7:
        options += [SoloDevelopment.METRIC_ILLUSION]
    if state.statements >= 4:
        options += [SoloDevelopment.RECAP]
    if plan.target_reentry or context.section_transition or context.phrase_position >= 0.9:
        options += [SoloDevelopment.RESOLVE]
    return tuple(options)


def build_solo_candidates(
    plan: DrumSoloPlan,
    context: DrummerRuntimeContext,
    state: DrumSoloState,
    *,
    legend: DrumLegendProjection | None = None,
    vocabulary_intents: tuple[DrumVocabularyIntent, ...] = (),
) -> tuple[SoloCandidate, ...]:
    """Build immediate solo gestures and score phrase-development alternatives."""
    plan.validate()
    context.validate()
    candidates: list[SoloCandidate] = []

    for development in _development_options(plan, context, state):
        if development in {SoloDevelopment.ADD_SPACE, SoloDevelopment.INTERNAL_REST}:
            gesture = DrumGesture(
                role=GestureRole.SPACE,
                tags=frozenset({"drum_solo", plan.arc.value, development.value}),
                provenance=("drum_player", "solo_engine"),
            )
        else:
            gesture = _statement_gesture(plan, state, development)

        score = 0.0
        reasons: list[tuple[str, float]] = []

        if development is SoloDevelopment.STATE and state.statements == 0:
            score += 0.55
            reasons.append(("clear_initial_statement", 0.55))

        if development is SoloDevelopment.REPEAT:
            v = 0.42 if state.motif_repetitions < 2 else -0.22
            score += v
            reasons.append(("motif_repetition", v))

        if development is SoloDevelopment.ORCHESTRATE and state.statements >= 1:
            score += 0.46
            reasons.append(("develop_by_orchestration", 0.46))

        if development in {SoloDevelopment.ADD_SPACE, SoloDevelopment.INTERNAL_REST}:
            v = 0.15 + 0.46 * plan.space_probability + 0.22 * context.ensemble_activity
            if state.spaces > state.statements * 0.7:
                v -= 0.25
            score += v
            reasons.append(("phrase_space", v))

        if development is SoloDevelopment.DISPLACE:
            v = 0.20 + 0.32 * plan.adventurousness
            score += v
            reasons.append(("rhythmic_displacement", v))

        if development is SoloDevelopment.THREE_BEAT_CYCLE:
            v = 0.18 + 0.40 * plan.adventurousness
            score += v
            reasons.append(("three_beat_development", v))

        if development is SoloDevelopment.METRIC_ILLUSION:
            v = 0.10 + 0.48 * plan.adventurousness
            score += v
            reasons.append(("metric_illusion", v))

        if development is SoloDevelopment.CONTRAST:
            v = 0.25 + 0.22 * min(1.0, state.statements / 6)
            score += v
            reasons.append(("contrast", v))

        if development is SoloDevelopment.RECAP:
            v = 0.30 + 0.22 * min(1.0, state.statements / 8)
            score += v
            reasons.append(("recapitulation", v))

        if development is SoloDevelopment.RESOLVE:
            v = 0.15
            if plan.target_reentry:
                v += 0.55
            if context.section_transition:
                v += 0.35
            if context.phrase_position >= 0.9:
                v += 0.25
            score += v
            reasons.append(("ensemble_reentry", v))

        shared_bonus, shared_reasons = _shared_method_bonus(
            plan, context, state, development
        )
        if shared_bonus:
            score += shared_bonus
            reasons.append((f"shared_solo:{shared_operation_for_drum_development(development).value}", shared_bonus))

        # Arc-specific shaping.
        if plan.arc is SoloArc.OPEN and development in {
            SoloDevelopment.STATE,
            SoloDevelopment.REPEAT,
            SoloDevelopment.ADD_SPACE,
        }:
            score += 0.20
            reasons.append(("open_arc", 0.20))
        elif plan.arc is SoloArc.DEVELOP and development in {
            SoloDevelopment.ORCHESTRATE,
            SoloDevelopment.DISPLACE,
            SoloDevelopment.CONTRAST,
        }:
            score += 0.22
            reasons.append(("develop_arc", 0.22))
        elif plan.arc in {SoloArc.INTENSIFY, SoloArc.CLIMAX} and development in {
            SoloDevelopment.THREE_BEAT_CYCLE,
            SoloDevelopment.METRIC_ILLUSION,
            SoloDevelopment.CONTRAST,
        }:
            score += 0.24
            reasons.append(("intensity_arc", 0.24))
        elif plan.arc in {SoloArc.RELEASE, SoloArc.REENTRY} and development in {
            SoloDevelopment.ADD_SPACE,
            SoloDevelopment.RECAP,
            SoloDevelopment.RESOLVE,
        }:
            score += 0.30
            reasons.append(("release_reentry_arc", 0.30))

        if legend is not None:
            delta, parts = legend_gesture_adjustment(gesture, legend)
            score += delta
            reasons.extend(parts)

        if vocabulary_intents:
            delta, parts = vocabulary_gesture_adjustment(gesture, vocabulary_intents)
            score += delta
            reasons.extend(parts)

        candidates.append(SoloCandidate(gesture, development, score, tuple(reasons)))

    return tuple(candidates)


def perform_one_solo_gesture(
    plan: DrumSoloPlan,
    context: DrummerRuntimeContext,
    state: DrumSoloState,
    *,
    legend: DrumLegendProjection | None = None,
    vocabulary_intents: tuple[DrumVocabularyIntent, ...] = (),
) -> SoloCandidate:
    """Choose and commit one solo gesture, then caller must listen/re-plan."""
    candidates = build_solo_candidates(
        plan,
        context,
        state,
        legend=legend,
        vocabulary_intents=vocabulary_intents,
    )
    chosen = max(candidates, key=lambda c: c.score)
    state.observe(chosen.gesture, chosen.development)
    return chosen
