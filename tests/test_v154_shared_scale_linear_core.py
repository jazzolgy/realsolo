from music_intelligence.harmony.jazz_harmony_core import (
    HarmonicEvidence,
    HarmonicFrame,
    HarmonySource,
)
from music_intelligence.harmony.scale_linear_core import (
    LinearDirection,
    LinearRouteKind,
    build_contextual_scale_field,
    build_linear_connection_affordances,
)


def ev(source, root, symbol, pcs):
    return HarmonicEvidence(
        source=source,
        root_pc=root,
        symbol=symbol,
        pitch_classes=frozenset(pcs),
    )


def test_scale_field_does_not_invent_seven_note_scale_from_symbol():
    frame = HarmonicFrame(expected=ev(HarmonySource.EXPECTED, 0, "Cm7", {0,3,7,10}))
    field = build_contextual_scale_field(frame)
    assert field.pitch_classes == frozenset({0,3,7,10})
    assert len(field.pitch_classes) == 4


def test_explicit_local_key_can_expand_contextual_scale_field():
    frame = HarmonicFrame(expected=ev(HarmonySource.EXPECTED, 0, "Cm7", {0,3,7,10}))
    field = build_contextual_scale_field(
        frame,
        local_key_pitch_classes=frozenset({0,2,3,5,7,9,10}),
    )
    assert field.pitch_classes == frozenset({0,2,3,5,7,9,10})
    assert field.color_pitch_classes == frozenset({2,5,9})


def test_stepwise_routes_are_immediate_affordances_not_future_lines():
    frame = HarmonicFrame(expected=ev(HarmonySource.EXPECTED, 0, "Cm7", {0,3,7,10}))
    routes = build_linear_connection_affordances(
        frame,
        current_pitch_class=0,
        local_key_pitch_classes=frozenset({0,2,3,5,7,9,10}),
    )
    asc = [x for x in routes if x.route is LinearRouteKind.DIATONIC_PASSING
           and x.direction is LinearDirection.ASCENDING]
    assert asc
    assert asc[0].immediate_pitch_classes == frozenset({2})


def test_future_harmony_exposes_approach_without_making_it_compulsory():
    c = ev(HarmonySource.EXPECTED, 0, "Cm7", {0,3,7,10})
    f = ev(HarmonySource.EXPECTED, 5, "F7", {5,9,0,3})
    routes = build_linear_connection_affordances(
        HarmonicFrame(expected=c, next_expected=f),
        current_pitch_class=3,
    )
    kinds = {x.route for x in routes}
    assert LinearRouteKind.CHORDAL in kinds
    assert LinearRouteKind.APPROACH in kinds
    assert LinearRouteKind.ANTICIPATION in kinds


def test_scale_fragment_requires_real_contextual_pitch_evidence():
    frame = HarmonicFrame(expected=ev(HarmonySource.EXPECTED, 0, "Cm7", {0,3,7,10}))
    without_key = build_linear_connection_affordances(frame, current_pitch_class=0)
    with_key = build_linear_connection_affordances(
        frame,
        current_pitch_class=0,
        local_key_pitch_classes=frozenset({0,2,3,5,7,9,10}),
    )
    assert all(x.route is not LinearRouteKind.SCALE_FRAGMENT for x in without_key)
    assert any(x.route is LinearRouteKind.SCALE_FRAGMENT for x in with_key)
