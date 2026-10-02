from music_intelligence.reasoning.solo_grammar import SoloDevelopmentOperation
from players.bass.phrase_intent import (
    BassPhraseContext,
    BassPhraseIntent,
    BassPhraseIntentKind,
)
from players.bass.solo_method import bass_shared_solo_options


def test_bass_can_consume_shared_solo_grammar():
    options = bass_shared_solo_options(
        BassPhraseContext(
            phrase_progress=.55,
            ensemble_activity=.4,
            soloist_phrase_ending=True,
        ),
        BassPhraseIntent(BassPhraseIntentKind.DEVELOP),
    )
    ops = {o.operation for o in options}
    assert SoloDevelopmentOperation.VARY in ops
    assert SoloDevelopmentOperation.DISPLACE in ops
