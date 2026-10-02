"""Scott LaFaro evidence-gated LegendProfile.

Seed tendencies are literature-grounded and intentionally modest. Project-source
audio observations must confirm/contextualize them before stronger promotion.
"""
from music_intelligence.legends.interfaces import LegendDomain, LegendProfileView
from music_intelligence.reasoning.legend_style_core import LegendProfile, StyleTendency


SCOTT_LAFARO_PROFILE = LegendProfile(
    profile_id="legend.scott_lafaro.online.v1",
    display_name="Scott LaFaro contextual bass/solo profile",
    instrument_family="bass",
    era_or_school="interactive_modern_jazz_trio",
    source_count=2,
    tendencies=(
        StyleTendency(
            tendency_id="lafaro.rhythmic_motif.persistence.v1",
            feature="solo.rhythmic_motif_persistence",
            context_tags=frozenset({"solo"}),
            weight=.18,
            confidence=.72,
            provenance=("literature:clark_2014",),
            note="Repeated rhythmic motifs may remain active across multiple bars.",
        ),
        StyleTendency(
            tendency_id="lafaro.rhythmic_displacement.v1",
            feature="solo.rhythmic_displacement",
            context_tags=frozenset({"solo", "develop"}),
            weight=.16,
            confidence=.70,
            provenance=("literature:clark_2014", "literature:nardis_comparative_2019"),
            note="Rhythmic displacement/polyrhythmic development is a recurring phrase device.",
        ),
        StyleTendency(
            tendency_id="lafaro.triplet_eighth_variety.v1",
            feature="solo.subdivision_variation",
            context_tags=frozenset({"solo"}),
            weight=.14,
            confidence=.68,
            provenance=("literature:nardis_comparative_2019",),
            note="Eighth-note and triplet contrast is used to develop phrasing.",
        ),
        StyleTendency(
            tendency_id="lafaro.linear_scale_arpeggio.v1",
            feature="solo.linear_scale_arpeggio_motion",
            context_tags=frozenset({"solo"}),
            weight=.15,
            confidence=.70,
            provenance=("literature:clark_2014", "literature:nardis_comparative_2019"),
            note="Scale/arpeggio motion can preserve a melodic line through chord changes.",
        ),
        StyleTendency(
            tendency_id="lafaro.productive_repetition.v1",
            feature="solo.productive_repetition",
            context_tags=frozenset({"solo", "develop"}),
            weight=.13,
            confidence=.68,
            provenance=("literature:clark_2014",),
            note="Repeated identity can be developmental material rather than template failure.",
        ),
    ),
    notes=(
        "Literature-seeded, evidence-gated profile. Interaction is intentionally "
        "not globally boosted: project-source phrase observations must establish "
        "when LaFaro answers, leads, grounds, or remains independent."
    ),
)

SCOTT_LAFARO_DOMAIN_FEATURES = {
    domain: ()
    for domain in LegendDomain
}
SCOTT_LAFARO_DOMAIN_FEATURES.update({
    LegendDomain.RHYTHM_SUBDIVISION: (
        "solo.rhythmic_displacement",
        "solo.subdivision_variation",
    ),
    LegendDomain.MOTIF_DEVELOPMENT: (
        "solo.rhythmic_motif_persistence",
        "solo.productive_repetition",
    ),
    LegendDomain.REPETITION_VARIATION: (
        "solo.rhythmic_motif_persistence",
        "solo.productive_repetition",
    ),
    LegendDomain.LINEAR_CONNECTION: (
        "solo.linear_scale_arpeggio_motion",
    ),
})

SCOTT_LAFARO_PROFILE_VIEW = LegendProfileView(
    legend_id="scott_lafaro",
    profile=SCOTT_LAFARO_PROFILE,
    domain_features=SCOTT_LAFARO_DOMAIN_FEATURES,
)
