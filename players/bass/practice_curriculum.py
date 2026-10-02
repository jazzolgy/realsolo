"""Bass practice curriculum derived from uploaded walking-bass method materials.

The curriculum stores *exercise constraints and evaluation goals*, not textbook
lines or transcriptions. It is designed to prevent the AI bassist from
overfitting to one walking formula.

Progression:
1. root orientation
2. interval/chord-tone connection
3. half-time approach-tone connection
4. quarter-note walking with scale/arpeggio freedom
5. mixed chordal/scalar/chromatic routes
6. anti-template variation across repeated choruses
7. rhythmic/articulation punctuation without losing the pulse
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class BassPracticeLevel(str, Enum):
    ROOT_ORIENTATION = "root_orientation"
    CHORD_TONE_CONNECTION = "chord_tone_connection"
    HALF_TIME_APPROACH = "half_time_approach"
    WALKING_CONNECTION = "walking_connection"
    MIXED_ROUTE = "mixed_route"
    ANTI_TEMPLATE = "anti_template"
    RHYTHMIC_PUNCTUATION = "rhythmic_punctuation"


@dataclass(frozen=True)
class BassPracticeExercise:
    exercise_id: str
    level: BassPracticeLevel
    description: str
    required_behaviors: tuple[str, ...]
    avoid_behaviors: tuple[str, ...] = ()
    repetitions: int = 4


@dataclass(frozen=True)
class BassPracticeEvaluation:
    pulse_continuity: float
    harmonic_orientation: float
    connection_quality: float
    contour_variety: float
    role_pattern_variety: float
    register_discipline: float
    ornament_restraint: float

    @property
    def total(self) -> float:
        values = (
            self.pulse_continuity,
            self.harmonic_orientation,
            self.connection_quality,
            self.contour_variety,
            self.role_pattern_variety,
            self.register_discipline,
            self.ornament_restraint,
        )
        return sum(values) / len(values)


def bebop_walking_practice_curriculum() -> tuple[BassPracticeExercise, ...]:
    """Return the current staged exercise set.

    These tasks abstract method-book principles; they contain no copied bass
    lines or literal exercises.
    """
    return (
        BassPracticeExercise(
            "root_map",
            BassPracticeLevel.ROOT_ORIENTATION,
            "Orient every harmony by its root before adding connective motion.",
            ("root_on_structural_arrival", "steady_pulse"),
            ("unmotivated_upper_register",),
        ),
        BassPracticeExercise(
            "chord_tone_routes",
            BassPracticeLevel.CHORD_TONE_CONNECTION,
            "Connect chord changes using chord members while preserving a clear bass floor.",
            ("chord_member_continuity", "next_root_awareness"),
            ("same_role_grid_every_bar",),
        ),
        BassPracticeExercise(
            "half_time_approach",
            BassPracticeLevel.HALF_TIME_APPROACH,
            "Practice two-feel with simple root/fifth support and restrained half-step approach to the next root.",
            ("root_fifth_center", "upper_or_lower_half_step_approach"),
            ("frequent_third_seventh_on_second_pulse", "automatic_fill"),
        ),
        BassPracticeExercise(
            "walking_four",
            BassPracticeLevel.WALKING_CONNECTION,
            "Walk quarter notes; use chord/scale material while the last beat may prepare the next harmony.",
            ("quarter_note_flow", "multiple_connection_routes"),
            ("approach_on_every_bar", "root_chordtone_chordtone_approach_template"),
        ),
        BassPracticeExercise(
            "mixed_routes",
            BassPracticeLevel.MIXED_ROUTE,
            "Alternate chordal, scalar and chromatic connective strategies over the same changes.",
            ("chordal_route", "scalar_route", "chromatic_route"),
            ("single_route_dominance",),
            repetitions=8,
        ),
        BassPracticeExercise(
            "repeat_chorus_variation",
            BassPracticeLevel.ANTI_TEMPLATE,
            "Repeat the same progression without repeating the same metric-role or contour template.",
            ("role_sequence_variation", "contour_variation", "stable_register_home"),
            ("literal_bar_template_repeat", "continuous_one_direction_motion"),
            repetitions=12,
        ),
        BassPracticeExercise(
            "pulse_with_punctuation",
            BassPracticeLevel.RHYTHMIC_PUNCTUATION,
            "Add occasional rhythmic/articulation punctuation while preserving smooth quarter-note flow.",
            ("swing_pulse_continuity", "sparse_punctuation"),
            ("constant_syncopation", "constant_ghosting", "pulse_disruption"),
            repetitions=8,
        ),
    )


def curriculum_feature_weights(level: BassPracticeLevel) -> dict[str, float]:
    """Return soft evaluator weights for one practice level."""
    base = {
        "pulse_continuity": 1.0,
        "harmonic_orientation": 1.0,
        "connection_quality": 1.0,
        "contour_variety": .65,
        "role_pattern_variety": .65,
        "register_discipline": .85,
        "ornament_restraint": .80,
    }
    if level is BassPracticeLevel.ROOT_ORIENTATION:
        base["harmonic_orientation"] = 1.45
        base["contour_variety"] = .20
    elif level is BassPracticeLevel.HALF_TIME_APPROACH:
        base["connection_quality"] = 1.25
        base["ornament_restraint"] = 1.20
    elif level is BassPracticeLevel.WALKING_CONNECTION:
        base["pulse_continuity"] = 1.30
        base["connection_quality"] = 1.20
    elif level is BassPracticeLevel.MIXED_ROUTE:
        base["role_pattern_variety"] = 1.20
        base["contour_variety"] = 1.00
    elif level is BassPracticeLevel.ANTI_TEMPLATE:
        base["role_pattern_variety"] = 1.45
        base["contour_variety"] = 1.20
    elif level is BassPracticeLevel.RHYTHMIC_PUNCTUATION:
        base["pulse_continuity"] = 1.40
        base["ornament_restraint"] = 1.35
    return base
