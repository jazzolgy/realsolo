"""Parker phrase-space prior from score-derived rest evidence."""
from pathlib import Path
import json

from music_intelligence.reasoning.legend_style_core import LegendProfile, StyleTendency


def load_phrase_space_statistics() -> dict:
    path = Path(__file__).with_name("data") / "phrase_space_stats.json"
    return json.loads(path.read_text(encoding="utf-8"))


PARKER_PHRASE_SPACE_PROFILE = LegendProfile(
    profile_id="legend.charlie_parker.phrase_space",
    display_name="Charlie Parker score-derived phrase-space prior",
    instrument_family="alto_saxophone",
    era_or_school="bebop",
    source_count=1461,
    tendencies=(
        StyleTendency("parker.space.half", "rest_half_beat", frozenset({"rest"}),
                      +.075, .74, ("digital_omnibook_derived_rests",),
                      "eighth-rest-scale punctuation is common"),
        StyleTendency("parker.space.one", "rest_one_beat", frozenset({"rest"}),
                      +.088, .76, ("digital_omnibook_derived_rests",),
                      "one-beat rests are the modal phrase-space category"),
        StyleTendency("parker.space.two", "rest_two_beats", frozenset({"rest"}),
                      +.052, .72, ("digital_omnibook_derived_rests",),
                      "half-bar space is substantial"),
        StyleTendency("parker.space.four_plus", "rest_four_beats_plus", frozenset({"rest"}),
                      +.018, .68, ("digital_omnibook_derived_rests",),
                      "full-bar or longer handoff is rarer but structurally valid"),
        StyleTendency("parker.space.ensemble", "ensemble_space", frozenset({"rest"}),
                      +.055, .78, ("digital_omnibook_derived_rests", "expert"),
                      "silence can be an active ensemble decision"),
    ),
    notes="Score-rest evidence only; not acoustic microtiming evidence.",
)
