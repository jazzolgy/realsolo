from fractions import Fraction

from music_intelligence.transcribe.rhythm import (
    QuantizationGrid,
    quantize_score_span,
    rest_for_gap,
    split_note_across_bars,
    tuplet_note,
)


def test_score_time_quantization_does_not_copy_microtiming_literally():
    span = quantize_score_span(
        1.018,
        1.493,
        grid=QuantizationGrid(step=Fraction(1, 2)),
    )
    assert span.onset == Fraction(1, 1)
    assert span.duration == Fraction(1, 2)


def test_note_crossing_barline_is_split_with_tie_chain():
    atoms = split_note_across_bars(
        span=__import__("music_intelligence.transcribe.notation", fromlist=["ScoreSpan"]).ScoreSpan(
            Fraction(7, 2), Fraction(1, 1)
        ),
        source_event_ids=("bass:note:1",),
        grid=QuantizationGrid(
            step=Fraction(1, 2),
            meter_numerator=4,
            meter_denominator=4,
        ),
    )
    assert len(atoms) == 2
    assert atoms[0].span == __import__("music_intelligence.transcribe.notation", fromlist=["ScoreSpan"]).ScoreSpan(
        Fraction(7, 2), Fraction(1, 2)
    )
    assert atoms[0].tie_to_next is True
    assert atoms[1].tie_from_previous is True


def test_positive_gap_can_be_made_explicit_as_rest():
    rest = rest_for_gap(Fraction(1), Fraction(3, 2))
    assert rest is not None
    assert rest.span.duration == Fraction(1, 2)
    assert rest.source_event_ids == ()


def test_arbitrary_tuplet_ratio_is_supported_without_artificial_maximum():
    atom = tuplet_note(
        onset=Fraction(0),
        duration=Fraction(1, 11),
        source_event_ids=("sax:11tuple:1",),
        actual=11,
        normal=8,
    )
    assert atom.tuplet is not None
    assert atom.tuplet.actual == 11
    assert atom.tuplet.normal == 8
