"""Source-derived drummer decision knowledge.

This is not Shared Core semantics.  It is drummer-owned interpretation of how
to realize time, interaction, orchestration, and vocabulary.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DrummerDecisionRule:
    rule_id: str
    source_id: str
    applies_to: frozenset[str]
    principle: str
    runtime_implication: str


DRUMMER_DECISION_RULES: tuple[DrummerDecisionRule, ...] = (
    DrummerDecisionRule(
        "moses_play_off_something",
        "moses_drum_wisdom",
        frozenset({"improvisation", "comping", "soloing"}),
        "A musical idea should have a reference: melody, bass line, vamp, another player, or internally heard material.",
        "Reject context-free decoration; candidate scoring should reward a perceptible musical referent.",
    ),
    DrummerDecisionRule(
        "moses_internal_hearing_before_external_reaction",
        "moses_drum_wisdom",
        frozenset({"listening", "interaction"}),
        "Internal hearing provides enough structural continuity to listen outward without losing the form/groove basis.",
        "Maintain a stable internal time/form reference while allocating attention to ensemble events.",
    ),
    DrummerDecisionRule(
        "riley_collective_time",
        "riley_beyond_bop",
        frozenset({"modern_jazz", "broken_time", "time_playing"}),
        "Time can emerge from the combined drum-set parts and ensemble rather than an invariant ride-cymbal ostinato.",
        "Allow irregular ride while preserving aggregate forward motion and readable ensemble pulse.",
    ),
    DrummerDecisionRule(
        "riley_hihat_counterpoint",
        "riley_beyond_bop",
        frozenset({"modern_jazz", "counterpoint"}),
        "Pedal hi-hat may act as an independent contrapuntal voice rather than only fixed 2-and-4 punctuation.",
        "Represent hi-hat as a candidate voice with its own interaction policy when style permits.",
    ),
    DrummerDecisionRule(
        "riley_listen_not_copy",
        "riley_beyond_bop",
        frozenset({"interaction", "comping"}),
        "Reaction to another player should be individualized; listening is the source, not literal imitation.",
        "Similarity to an ensemble event is one option; transformation, continuation, or contrast remain candidates.",
    ),
    DrummerDecisionRule(
        "riley_two_feel_activity",
        "riley_art_bop",
        frozenset({"two_feel", "jazz"}),
        "Two-feel is less active than four and should keep the cymbal flow while reducing surface activity.",
        "Lower comping density and preserve phrase continuity rather than simply halving event count mechanically.",
    ),
    DrummerDecisionRule(
        "riley_uptempo_economy",
        "riley_art_bop",
        frozenset({"uptempo", "jazz"}),
        "At very fast tempi, preserve ride flow and use lighter, simpler accompaniment before adding complexity.",
        "Tempo should reduce absolute microtiming freedom and penalize unnecessarily dense limb activity.",
    ),
    DrummerDecisionRule(
        "spagnardi_fill_function",
        "spagnardi_big_band_fills",
        frozenset({"fill", "setup", "big_band"}),
        "A fill can prepare and lead the ensemble into a figure while adding color, intensity, and momentum.",
        "Fill continuation needs a target event and must evaluate whether to continue, stop, or resolve into that target.",
    ),
    DrummerDecisionRule(
        "holland_space_is_material",
        "holland_complete_fills",
        frozenset({"fill", "space"}),
        "The musical result includes both played notes and the space between them.",
        "Rest/space must remain a first-class fill event and candidate.",
    ),
    DrummerDecisionRule(
        "holland_crash_optional",
        "holland_complete_fills",
        frozenset({"fill", "crash"}),
        "A crash after a fill is optional; the player may return directly to the groove.",
        "Do not hard-code fill -> crash resolution.",
    ),
    DrummerDecisionRule(
        "plainfield_independence_as_orchestration",
        "plainfield_advanced_concepts",
        frozenset({"independence", "contemporary"}),
        "Coordination studies are applied by moving rhythmic material among voices/limbs and combining roles.",
        "Pattern transformations should include voice reassignment subject to physical feasibility.",
    ),
    DrummerDecisionRule(
        "plainfield_afrocuban_clave_relation",
        "plainfield_advanced_concepts",
        frozenset({"afro_cuban", "clave"}),
        "Clave orientation and its relationship to cascara/groove patterns are structural, not interchangeable decoration.",
        "Afro-Cuban candidate selection must carry clave direction/context and reject incompatible pattern combinations.",
    ),
    DrummerDecisionRule(
        "badness_four_limb_reality",
        "badness_drum_programming",
        frozenset({"programming", "physical_feasibility"}),
        "A realistic drum part must respect that one drummer has four limbs and kit voices interact physically.",
        "Every generated gesture/pattern transformation must pass limb occupancy and reachability constraints.",
    ),
    DrummerDecisionRule(
        "badness_kit_interdependence",
        "badness_drum_programming",
        frozenset({"groove", "arrangement"}),
        "Kick, snare, cymbals, toms, and other instruments work as a coordinated system rather than isolated loops.",
        "Evaluate groove at multi-voice level and against bass/ensemble relationships.",
    ),
)


def rules_for(*tags: str) -> tuple[DrummerDecisionRule, ...]:
    wanted = set(tags)
    return tuple(rule for rule in DRUMMER_DECISION_RULES if wanted & set(rule.applies_to))
