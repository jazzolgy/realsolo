"""Evidence-gated Eliot Zigmund profile.

Vocabulary is available from verified source observations. Broader style
tendencies remain empty until multiple independent recordings support them.
"""
from music_intelligence.legends.interfaces import LegendDomain, LegendProfileView
from music_intelligence.reasoning.legend_style_core import LegendProfile

ELIOT_ZIGMUND_PROFILE = LegendProfile(
    profile_id="legend.eliot_zigmund.online.v1",
    display_name="Eliot Zigmund contextual decision profile",
    instrument_family="drums",
    era_or_school="modern_jazz_piano_trio",
    source_count=1,
    tendencies=(),
    notes=(
        "One source-grounded drum-solo vocabulary set is available; "
        "do not infer broad style tendencies from a single recording."
    ),
)

ELIOT_ZIGMUND_PROFILE_VIEW = LegendProfileView(
    legend_id="eliot_zigmund",
    profile=ELIOT_ZIGMUND_PROFILE,
    domain_features={domain: () for domain in LegendDomain},
)
