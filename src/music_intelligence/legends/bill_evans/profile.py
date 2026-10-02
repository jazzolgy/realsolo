"""Bill Evans evidence-gated LegendProfile.

This profile is intentionally empty until source-grounded observations are
promoted from the Bill Evans research corpus. Do not fill tendencies from
general jazz knowledge or reputation.
"""
from music_intelligence.legends.interfaces import LegendDomain, LegendProfileView
from music_intelligence.reasoning.legend_style_core import LegendProfile

BILL_EVANS_PROFILE = LegendProfile(
    profile_id="legend.bill_evans.online.v1",
    display_name="Bill Evans contextual decision profile",
    instrument_family="piano",
    era_or_school="modern_jazz_piano_trio",
    source_count=0,
    tendencies=(),
    notes=(
        "Evidence-gated scaffold. Promote only source-grounded Bill Evans "
        "observations from research/legends/bill_evans/."
    ),
)

BILL_EVANS_DOMAIN_FEATURES = {
    domain: ()
    for domain in LegendDomain
}

BILL_EVANS_PROFILE_VIEW = LegendProfileView(
    legend_id="bill_evans",
    profile=BILL_EVANS_PROFILE,
    domain_features=BILL_EVANS_DOMAIN_FEATURES,
)
