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


def test_bill_evans_vocabulary_contains_only_promoted_source_grounded_items():
    query = VocabularyQuery(
        "bill_evans",
        domain=LegendDomain.ENSEMBLE_INTERACTION,
        context_tags=frozenset({"fast_swing","bass_foreground","piano_trio","autumn_leaves"}),
    )
    items = BILL_EVANS_VOCABULARY_INDEX.query(query)
    assert items
    assert all(item.source_id == "BE-003" for item in items)
    assert all(item.provenance for item in items)
    assert all(not item.literal_representation for item in items)


def test_bill_evans_runtime_blend_is_valid_even_before_tendencies_are_promoted():
    BILL_EVANS_RUNTIME_BLEND.validate()


def test_bill_evans_autumn_leaves_motif_pattern_is_queryable_for_piano():
    query = VocabularyQuery(
        "bill_evans",
        domain=LegendDomain.MOTIF_DEVELOPMENT,
        context_tags=frozenset({"fast_swing","piano_solo","A_section","autumn_leaves"}),
        target_instrument="piano",
    )
    items = BILL_EVANS_VOCABULARY_INDEX.query(query)
    assert items
    assert items[0].vocabulary_id == "BE-AL-A1-STRUCTURAL-DESCENT-001"
