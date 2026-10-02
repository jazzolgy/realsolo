"""Scott LaFaro evidence-gated LegendProfile.

No tendency is populated until verified phrase-level observations are promoted
from research/legends/scott_lafaro/.
"""
from music_intelligence.legends.interfaces import LegendDomain, LegendProfileView
from music_intelligence.reasoning.legend_style_core import LegendProfile

SCOTT_LAFARO_PROFILE = LegendProfile(
    profile_id="legend.scott_lafaro.online.v1",
    display_name="Scott LaFaro contextual bass/solo profile",
    instrument_family="bass",
    era_or_school="interactive_modern_jazz_trio",
    source_count=0,
    tendencies=(),
    notes=(
        "Evidence-gated scaffold. Promote only verified phrase-level Scott "
        "LaFaro observations with source/personnel provenance."
    ),
)

SCOTT_LAFARO_DOMAIN_FEATURES = {domain: () for domain in LegendDomain}

SCOTT_LAFARO_PROFILE_VIEW = LegendProfileView(
    legend_id="scott_lafaro",
    profile=SCOTT_LAFARO_PROFILE,
    domain_features=SCOTT_LAFARO_DOMAIN_FEATURES,
)
