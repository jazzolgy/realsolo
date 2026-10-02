"""v1.32 score-derived Parker phrase-space prior.

This evidence comes from rest durations in a 46-tune digital Omnibook-derived
analysis. It is intentionally lower-confidence than verified recording evidence.
"""
from music_intelligence.reasoning.legend_style_core import LegendProfile, StyleTendency

PARKER_PHRASE_SPACE_PROFILE = LegendProfile(
    profile_id="legend.charlie_parker.phrase_space.v132",
    display_name="Charlie Parker score-derived phrase-space prior v1.32",
    instrument_family="alto_saxophone",
    era_or_school="bebop",
    source_count=1461,
    tendencies=(
        StyleTendency(
            "parker.space.half", "rest_half_beat", frozenset({"rest"}),
            +0.075, 0.74, ("digital_omnibook_derived_rests",),
            "eighth-rest-scale punctuation is common",
        ),
        StyleTendency(
            "parker.space.one", "rest_one_beat", frozenset({"rest"}),
            +0.088, 0.76, ("digital_omnibook_derived_rests",),
            "one-beat rests are the modal phrase-space category",
        ),
        StyleTendency(
            "parker.space.two", "rest_two_beats", frozenset({"rest"}),
            +0.052, 0.72, ("digital_omnibook_derived_rests",),
            "half-bar space is substantial, not exceptional",
        ),
        StyleTendency(
            "parker.space.four_plus", "rest_four_beats_plus", frozenset({"rest"}),
            +0.018, 0.68, ("digital_omnibook_derived_rests",),
            "full-bar or longer handoff is rarer but structurally valid",
        ),
        StyleTendency(
            "parker.space.ensemble", "ensemble_space", frozenset({"rest"}),
            +0.055, 0.78, ("digital_omnibook_derived_rests", "expert"),
            "silence can be an active phrase and ensemble decision",
        ),
    ),
    notes=(
        "Derived from score-level rests >= 0.5 quarter across 46 Omnibook tunes. "
        "Do not use this profile to infer acoustic microtiming or exact phrase-entry beat."
    ),
)
