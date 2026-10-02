from fractions import Fraction

from music_intelligence.transcribe import (
    ChartMeasure,
    ChordChange,
    ChordChart,
    ChordSymbol,
    NavigationMark,
)
from music_intelligence.transcribe.chord_chart_quality import (
    ChartIssueSeverity,
    audit_chord_chart,
)


def test_audit_flags_ds_without_segno_and_to_coda_without_coda():
    chart = ChordChart(
        "bad:nav",
        "Bad Nav",
        (
            ChartMeasure(
                1,
                (ChordChange(Fraction(0), ChordSymbol(0, "maj7")),),
                navigation_marks=(NavigationMark.DS,),
            ),
            ChartMeasure(
                2,
                (ChordChange(Fraction(0), ChordSymbol(7, "7")),),
                navigation_marks=(NavigationMark.TO_CODA,),
            ),
        ),
    )

    report = audit_chord_chart(chart)
    codes = {i.code for i in report.issues}

    assert report.has_errors
    assert "ds-without-segno" in codes
    assert "to-coda-without-coda" in codes


def test_audit_accepts_basic_valid_segno_coda_navigation():
    chart = ChordChart(
        "ok:nav",
        "Good Nav",
        (
            ChartMeasure(
                1,
                (ChordChange(Fraction(0), ChordSymbol(0, "maj7")),),
                navigation_marks=(NavigationMark.SEGNO,),
            ),
            ChartMeasure(
                2,
                (ChordChange(Fraction(0), ChordSymbol(2, "m7")),),
                navigation_marks=(NavigationMark.TO_CODA,),
            ),
            ChartMeasure(
                3,
                (ChordChange(Fraction(0), ChordSymbol(7, "7")),),
                navigation_marks=(NavigationMark.DS,),
            ),
            ChartMeasure(
                4,
                (ChordChange(Fraction(0), ChordSymbol(0, "maj7")),),
                navigation_marks=(NavigationMark.CODA, NavigationMark.FINE),
            ),
        ),
    )

    report = audit_chord_chart(chart)

    assert report.has_errors is False
    assert all(i.severity is not ChartIssueSeverity.ERROR for i in report.issues)
