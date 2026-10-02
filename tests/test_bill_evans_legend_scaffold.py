from music_intelligence.legends import LegendDomain, VocabularyQuery
from music_intelligence.legends.bill_evans import (
    BILL_EVANS_PROFILE,
    BILL_EVANS_PROFILE_VIEW,
    BILL_EVANS_RUNTIME_BLEND,
    BILL_EVANS_VOCABULARY_INDEX,
)


def test_bill_evans_is_first_class_evidence_gated_legend():
    assert BILL_EVANS_PROFILE.profile_id.startswith("legend.bill_evans.")
    assert BILL_EVANS_PROFILE.instrument_family == "piano"
    assert BILL_EVANS_PROFILE.source_count == 0
    assert BILL_EVANS_PROFILE.tendencies == ()


def test_bill_evans_profile_exposes_all_domains_without_invented_evidence():
    coverage = BILL_EVANS_PROFILE_VIEW.coverage()
    assert set(coverage) == set(LegendDomain)
    assert all(count == 0 for count in coverage.values())


def test_bill_evans_vocabulary_starts_empty_until_source_promotion():
    query = VocabularyQuery("bill_evans", domain=LegendDomain.ENSEMBLE_INTERACTION)
    assert BILL_EVANS_VOCABULARY_INDEX.query(query) == ()


def test_bill_evans_runtime_blend_is_valid_even_before_tendencies_are_promoted():
    BILL_EVANS_RUNTIME_BLEND.validate()
