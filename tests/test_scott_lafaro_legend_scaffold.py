from music_intelligence.legends import VocabularyQuery
from music_intelligence.legends.scott_lafaro import (
    SCOTT_LAFARO_PROFILE,
    SCOTT_LAFARO_PROFILE_VIEW,
    SCOTT_LAFARO_VOCABULARY_INDEX,
)


def test_lafaro_profile_is_evidence_gated_and_literature_seeded():
    assert SCOTT_LAFARO_PROFILE.instrument_family == "bass"
    assert SCOTT_LAFARO_PROFILE.source_count == 2
    assert SCOTT_LAFARO_PROFILE.tendencies
    assert all(t.provenance for t in SCOTT_LAFARO_PROFILE.tendencies)
    assert all(0.0 < t.confidence < 1.0 for t in SCOTT_LAFARO_PROFILE.tendencies)
    assert SCOTT_LAFARO_PROFILE_VIEW.legend_id == "scott_lafaro"


def test_lafaro_profile_exposes_motif_and_rhythm_domains_only_where_seeded():
    from music_intelligence.legends import LegendDomain
    motif = SCOTT_LAFARO_PROFILE_VIEW.tendencies(
        domain=LegendDomain.MOTIF_DEVELOPMENT,
        active_tags=("solo", "develop"),
    )
    rhythm = SCOTT_LAFARO_PROFILE_VIEW.tendencies(
        domain=LegendDomain.RHYTHM_SUBDIVISION,
        active_tags=("solo", "develop"),
    )
    assert any(t.feature == "solo.productive_repetition" for t in motif)
    assert any(t.feature == "solo.rhythmic_displacement" for t in rhythm)


def test_lafaro_vocabulary_does_not_invent_material():
    assert SCOTT_LAFARO_VOCABULARY_INDEX.query(
        VocabularyQuery(legend_id="scott_lafaro")
    ) == ()
    assert SCOTT_LAFARO_VOCABULARY_INDEX.query(
        VocabularyQuery(legend_id="bill_evans")
    ) == ()
