from music_intelligence.reasoning.solo_grammar import SoloDevelopmentOperation
from players.sax.solo_method import sax_shared_solo_options


def test_sax_can_consume_shared_solo_grammar():
    options = sax_shared_solo_options(
        phrase_maturity=.6,
        ensemble_activity=.35,
        future_harmony_available=True,
        interaction_role="ANSWER",
    )
    ops = {o.operation for o in options}
    assert SoloDevelopmentOperation.TARGET_NEXT_HARMONY in ops
    assert SoloDevelopmentOperation.ANSWER in ops
