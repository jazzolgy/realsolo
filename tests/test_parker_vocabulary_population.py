from music_intelligence.legends.interfaces import (
    LegendDomain,
    VocabularyQuery,
    VocabularyUseType,
)
from music_intelligence.legends.parker import PARKER_VOCABULARY_INDEX


def test_parker_vocabulary_is_no_longer_empty():
    assert len(PARKER_VOCABULARY_INDEX.items) >= 12


def test_parker_vocabulary_contains_existing_research_domains():
    ids={x.vocabulary_id for x in PARKER_VOCABULARY_INDEX.items}
    assert "parker.vocab.close_approach_target" in ids
    assert "parker.vocab.wide_leap_contrary_recovery" in ids
    assert "parker.vocab.rest_one_beat" in ids
    assert "parker.vocab.ensemble_space_handoff" in ids


def test_parker_vocabulary_is_queryable_for_tenor_sax():
    rows=PARKER_VOCABULARY_INDEX.query(VocabularyQuery(
        legend_id="charlie_parker",
        domain=LegendDomain.LINEAR_CONNECTION,
        target_instrument="tenor_sax",
        limit=16,
    ))
    assert rows
    assert all("charlie_parker" in x.context_tags for x in rows)


def test_aggregate_evidence_does_not_invent_literal_notes():
    derived=[
        x for x in PARKER_VOCABULARY_INDEX.items
        if "pedagogical_symbolic_131" in x.provenance
        or "PARKER_ONLINE_PROFILE" in x.provenance
    ]
    assert derived
    assert all(not x.literal_representation for x in derived)
    assert all(
        VocabularyUseType.LITERAL_QUOTE not in x.candidate_uses
        for x in derived
    )


def test_literal_loader_contract_can_support_direct_use_when_data_arrives():
    # Current repository has aggregate Parker lick statistics, not individual
    # exact note/rhythm payloads. Literal direct-use therefore activates only
    # when vocabulary*.json contains a real literal_representation.
    literal=[x for x in PARKER_VOCABULARY_INDEX.items if x.literal_representation]
    for item in literal:
        assert VocabularyUseType.LITERAL_QUOTE in item.candidate_uses



def test_all_four_recovered_lick_sheet_items_are_in_parker_vocabulary():
    ids={x.vocabulary_id for x in PARKER_VOCABULARY_INDEX.items}
    assert {
        "parker.source.licksheet.ii_v_i.honeysuckle",
        "parker.source.licksheet.ii_v_i.dm_shape",
        "parker.source.licksheet.major.cmaj_shape",
        "parker.source.licksheet.anthropology_opening",
    }.issubset(ids)


def test_recovered_source_locators_do_not_enable_literal_quote_before_note_verification():
    recovered=[
        x for x in PARKER_VOCABULARY_INDEX.items
        if x.source_id=="cp_charlie_parker_licks_pdf"
    ]
    assert len(recovered)==4
    assert all("source_image_verified" in x.provenance for x in recovered)
    assert all("note_payload_pending" in x.provenance for x in recovered)
    assert all(not x.literal_representation for x in recovered)
    assert all(
        VocabularyUseType.LITERAL_QUOTE not in x.candidate_uses
        for x in recovered
    )
