from music_intelligence.reasoning.solo_grammar import (
    SoloArc,
    SoloDevelopmentOperation,
    SoloMethodContext,
    shared_solo_method_options,
)


def test_shared_solo_grammar_is_instrument_neutral():
    ctx = SoloMethodContext(
        phrase_maturity=.6,
        ensemble_activity=.8,
        phrase_space_available=.6,
        future_harmony_available=True,
        interaction_role="ANSWER",
    )
    options = shared_solo_method_options(ctx, arc=SoloArc.DEVELOP)
    ops = {x.operation for x in options}
    assert SoloDevelopmentOperation.VARY in ops
    assert SoloDevelopmentOperation.DISPLACE in ops
    assert SoloDevelopmentOperation.ADD_SPACE in ops
    assert SoloDevelopmentOperation.TARGET_NEXT_HARMONY in ops
    assert SoloDevelopmentOperation.ANSWER in ops


def test_repetition_pressure_is_shared_methodology():
    early = shared_solo_method_options(SoloMethodContext(recent_repetition_count=0))
    repeated = shared_solo_method_options(SoloMethodContext(recent_repetition_count=3))
    e = next(x.weight for x in early if x.operation is SoloDevelopmentOperation.REPEAT)
    r = next(x.weight for x in repeated if x.operation is SoloDevelopmentOperation.REPEAT)
    assert r < e


def test_shared_solo_options_never_contain_future_notes():
    options = shared_solo_method_options(
        SoloMethodContext(future_harmony_available=True)
    )
    assert all(not hasattr(x, "future_notes") for x in options)
    assert all(not hasattr(x, "phrase_sequence") for x in options)
