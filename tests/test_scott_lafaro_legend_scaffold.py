from music_intelligence.legends import VocabularyQuery
from music_intelligence.legends.scott_lafaro import (
    SCOTT_LAFARO_PROFILE,
    SCOTT_LAFARO_PROFILE_VIEW,
    SCOTT_LAFARO_VOCABULARY_INDEX,
)


def test_lafaro_profile_starts_evidence_gated_and_empty():
    assert SCOTT_LAFARO_PROFILE.instrument_family == "bass"
    assert SCOTT_LAFARO_PROFILE.source_count == 0
    assert SCOTT_LAFARO_PROFILE.tendencies == ()
    assert SCOTT_LAFARO_PROFILE_VIEW.legend_id == "scott_lafaro"


def test_lafaro_vocabulary_does_not_invent_material():
    assert SCOTT_LAFARO_VOCABULARY_INDEX.query(
        VocabularyQuery(legend_id="scott_lafaro")
    ) == ()
    assert SCOTT_LAFARO_VOCABULARY_INDEX.query(
        VocabularyQuery(legend_id="bill_evans")
    ) == ()
