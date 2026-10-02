from players.sax import SaxExpressionContext, choose_sax_expression


def test_short_note_is_articulated_without_pitch_change():
    d = choose_sax_expression(
        SaxExpressionContext(67, 65, 0.5, 1.0, 0.2, 0.3)
    )
    assert "short" in d.tags


def test_low_long_note_can_be_subtone_and_breathy():
    d = choose_sax_expression(
        SaxExpressionContext(55, 57, 1.0, 2.0, 0.3, 0.25)
    )
    assert "subtone" in d.tags
    assert "breathy" in d.tags


def test_long_phrase_end_can_vibrate_and_fall():
    d = choose_sax_expression(
        SaxExpressionContext(69, 67, 1.0, 3.0, 0.95, 0.4)
    )
    assert "vibrato" in d.tags
    assert "fall" in d.tags


def test_expression_policy_limits_color_stacking():
    d = choose_sax_expression(
        SaxExpressionContext(59, 50, 1.25, 3.0, 0.9, 0.2)
    )
    assert len(d.tags) <= 3
