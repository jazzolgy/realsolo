"""Parker online LegendProfile: candidate-policy bias, never future-note scripting."""
from music_intelligence.reasoning.legend_style_core import LegendProfile, StyleTendency

PARKER_ONLINE_PROFILE = LegendProfile(
    profile_id="legend.charlie_parker.online.v1",
    display_name="Charlie Parker online decision profile",
    instrument_family="alto_saxophone",
    era_or_school="bebop",
    source_count=4,
    tendencies=(
        StyleTendency("parker.sync.entry","anticipation",frozenset({"anticipation"}),+.18,.99,("omnibook","expert"),"favor meaningful offbeat/late entry"),
        StyleTendency("parker.close.pass","passing",frozenset({"passing"}),+.10,.99,("omnibook","expert"),"close connector around stable targets"),
        StyleTendency("parker.close.neighbor","neighbor",frozenset({"neighbor"}),+.10,.99,("omnibook","expert"),"neighbor motion as melodic glue"),
        StyleTendency("parker.close.approach","close_approach",frozenset({"close_approach"}),+.12,.99,("omnibook","book_or_paper","expert"),"semitone/step approach to target"),
        StyleTendency("parker.alt.directed","altered",frozenset({"altered","directed_target"}),+.12,.99,("book_or_paper","expert"),"altered color is welcome when direction is audible"),
        StyleTendency("parker.alt.resolve","resolution_path",frozenset({"altered","resolution_path"}),+.12,.99,("book_or_paper","expert"),"altered chains may continue when they form a route"),
        StyleTendency("parker.space.handoff","ensemble_space",frozenset({"ensemble_space"}),+.10,.99,("omnibook","expert"),"space may foreground rhythm section"),
        StyleTendency("parker.triplet.context","triplet",frozenset({"triplet"}),+.05,.99,("omnibook",),"triplets are contextual insertions, not constant surface"),
        StyleTendency("parker.long.sync","syncopated_long_tone",frozenset({"syncopated_long_tone"}),+.14,.99,("omnibook","expert"),"held notes often gain life from offbeat/anticipated entry"),
        StyleTendency("parker.downbeat.hold","routine_downbeat_long_tone",frozenset({"routine_downbeat_long_tone"}),-.18,.99,("expert",),"avoid repeated unmotivated beat-1 holds"),
        StyleTendency("parker.wide.repeat","repeated_wide_leap",frozenset({"repeated_wide_leap"}),-.22,.99,("omnibook","book_or_paper","expert"),"wide leaps are events, not default locomotion"),
        StyleTendency("parker.maj7.11","exposed_maj7_natural11",frozenset({"exposed_maj7_natural11"}),-.24,.99,("expert",),"requires passing/enclosure/suspension justification"),
    ),
    notes="First high-resolution legend profile. Current ensemble evidence retains override authority.",
)
