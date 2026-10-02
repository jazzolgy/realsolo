"""Canonical Charlie Parker LegendProfileView and runtime blend."""
from music_intelligence.reasoning.legend_style_core import LegendBlend, LegendProfile, StyleTendency
from music_intelligence.legends.interfaces import LegendDomain, LegendProfileView

from .conditional_prior import PARKER_SYMBOLIC_MOTION_PROFILE
from .phrase_prior import PARKER_PHRASE_SPACE_PROFILE


PARKER_ONLINE_PROFILE = LegendProfile(
    profile_id="legend.charlie_parker.online",
    display_name="Charlie Parker online decision profile",
    instrument_family="alto_saxophone",
    era_or_school="bebop",
    source_count=4,
    tendencies=(
        StyleTendency("parker.sync.entry","anticipation",frozenset({"anticipation"}),+.18,.99,("omnibook","expert"),"favor meaningful offbeat/late entry"),
        StyleTendency("parker.close.pass","passing",frozenset({"passing"}),+.10,.99,("omnibook","expert"),"close connector around stable targets"),
        StyleTendency("parker.close.neighbor","neighbor",frozenset({"neighbor"}),+.10,.99,("omnibook","expert"),"neighbor motion as melodic glue"),
        StyleTendency("parker.close.approach","close_approach",frozenset({"close_approach"}),+.12,.99,("omnibook","book_or_paper","expert"),"step/semitone approach to target"),
        StyleTendency("parker.alt.directed","altered",frozenset({"altered","directed_target"}),+.12,.99,("book_or_paper","expert"),"altered color with audible direction"),
        StyleTendency("parker.alt.resolve","resolution_path",frozenset({"altered","resolution_path"}),+.12,.99,("book_or_paper","expert"),"altered chains may continue when they form a route"),
        StyleTendency("parker.space.handoff","ensemble_space",frozenset({"ensemble_space"}),+.10,.99,("omnibook","expert"),"space may foreground rhythm section"),
        StyleTendency("parker.triplet.context","triplet",frozenset({"triplet"}),+.05,.99,("omnibook",),"triplets are contextual insertions"),
        StyleTendency("parker.long.sync","syncopated_long_tone",frozenset({"syncopated_long_tone"}),+.14,.99,("omnibook","expert"),"held notes gain life from offbeat entry"),
        StyleTendency("parker.downbeat.hold","routine_downbeat_long_tone",frozenset({"routine_downbeat_long_tone"}),-.18,.99,("expert",),"avoid repeated unmotivated beat-1 holds"),
        StyleTendency("parker.wide.repeat","repeated_wide_leap",frozenset({"repeated_wide_leap"}),-.22,.99,("omnibook","book_or_paper","expert"),"wide leaps are events"),
        StyleTendency("parker.maj7.11","exposed_maj7_natural11",frozenset({"exposed_maj7_natural11"}),-.24,.99,("expert",),"requires passing/enclosure/suspension justification"),
    ),
    notes="Current ensemble evidence retains override authority.",
)

# Canonical runtime evidence blend. The weights remain evidence-class bounds,
# not a scalar claim that Parker is a percentage of the final player.
PARKER_RUNTIME_BLEND = LegendBlend((
    (PARKER_ONLINE_PROFILE, 1.0),
    (PARKER_SYMBOLIC_MOTION_PROFILE, .65),
    (PARKER_PHRASE_SPACE_PROFILE, .55),
))

_DOMAIN_FEATURES = {
    LegendDomain.HARMONY_TARGET_SELECTION: frozenset({"altered", "exposed_maj7_natural11"}),
    LegendDomain.LINEAR_CONNECTION: frozenset({
        "passing", "neighbor", "close_approach", "step_motion", "within_p4_motion",
        "contrary_recovery", "recovery_within_p4", "wide_leap", "compound_span_pressure",
    }),
    LegendDomain.PHRASE_ENTRANCE: frozenset({"anticipation", "syncopated_long_tone", "routine_downbeat_long_tone"}),
    LegendDomain.PHRASE_ENDING: frozenset({"structural_terminal_long_tone"}),
    LegendDomain.BREATH_SPACE: frozenset({"rest_half_beat","rest_one_beat","rest_two_beats","rest_four_beats_plus","ensemble_space"}),
    LegendDomain.RHYTHM_SUBDIVISION: frozenset({"triplet"}),
    LegendDomain.INTERVAL_LEAP_GRAMMAR: frozenset({"wide_leap","repeated_wide_leap","contrary_recovery","recovery_within_p4","compound_span_pressure"}),
    LegendDomain.TENSION_RELEASE: frozenset({"altered","resolution_path","exposed_maj7_natural11"}),
    LegendDomain.ENSEMBLE_INTERACTION: frozenset({"ensemble_space"}),
}

PARKER_PROFILE_VIEW = LegendProfileView(
    legend_id="charlie_parker",
    profiles=PARKER_RUNTIME_BLEND.profiles,
    domain_features=_DOMAIN_FEATURES,
)
