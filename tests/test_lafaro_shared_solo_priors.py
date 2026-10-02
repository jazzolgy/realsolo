from music_intelligence.legends.scott_lafaro import SCOTT_LAFARO_PROFILE_VIEW
from music_intelligence.reasoning.solo_grammar import (
    SoloArc,
    SoloDevelopmentOperation,
    SoloMethodContext,
    apply_legend_solo_priors,
    shared_solo_method_options,
)


def by_op(options):
    return {x.operation: x for x in options}


def test_lafaro_seed_priors_bias_shared_solo_operations_without_future_notes():
    base = shared_solo_method_options(
        SoloMethodContext(
            phrase_maturity=.55,
            tension=.45,
            ensemble_activity=.4,
            future_harmony_available=True,
        ),
        arc=SoloArc.DEVELOP,
    )
    biased = apply_legend_solo_priors(
        base,
        SCOTT_LAFARO_PROFILE_VIEW,
        active_tags=("solo", "develop"),
    )
    b = by_op(base)
    x = by_op(biased)

    assert x[SoloDevelopmentOperation.DISPLACE].weight > b[SoloDevelopmentOperation.DISPLACE].weight
    assert x[SoloDevelopmentOperation.REPEAT].weight > b[SoloDevelopmentOperation.REPEAT].weight
    assert x[SoloDevelopmentOperation.SEQUENCE].weight > b[SoloDevelopmentOperation.SEQUENCE].weight
    assert any(
        "legend:scott_lafaro:" in reason
        for option in biased
        for reason in option.reasons
    )


def test_unmapped_legend_features_do_not_create_pitch_sequences():
    options = apply_legend_solo_priors(
        (),
        SCOTT_LAFARO_PROFILE_VIEW,
        active_tags=("solo", "develop"),
    )
    assert all(hasattr(x, "operation") and hasattr(x, "weight") for x in options)
    assert all(not hasattr(x, "future_notes") for x in options)
