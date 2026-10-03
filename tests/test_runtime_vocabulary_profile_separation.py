from music_intelligence.legends.bill_evans import BILL_EVANS_PROFILE_VIEW, BILL_EVANS_VOCABULARY_INDEX
from music_intelligence.legends.scott_lafaro import SCOTT_LAFARO_VOCABULARY_INDEX
from music_intelligence.reasoning.runtime_vocabulary import select_runtime_vocabulary_sources


def test_vocabulary_availability_is_independent_from_profile_tendencies():
    # Bill Evans profile may remain evidence-gated/empty while source-grounded
    # vocabulary is available. Runtime selection must not conflate the two.
    assert BILL_EVANS_VOCABULARY_INDEX.items
    assert not BILL_EVANS_PROFILE_VIEW.profile.tendencies

    choices=select_runtime_vocabulary_sources(showcase=True)
    assert any(x.legend_id=="bill_evans" and x.player_id=="piano" for x in choices)


def test_lafaro_source_grounded_vocabulary_is_reachable_in_showcase():
    assert SCOTT_LAFARO_VOCABULARY_INDEX.items
    choices=select_runtime_vocabulary_sources(showcase=True)
    assert any(x.legend_id=="scott_lafaro" and x.player_id=="bass" for x in choices)
