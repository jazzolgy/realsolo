from fractions import Fraction

import pytest

from music_intelligence.transcribe import (
    LeadSheetProjection,
    OutputProfile,
    project_lead_sheet,
)
from music_intelligence.transcribe.chord_chart import (
    ChartMeasure,
    ChordChange,
    ChordChart,
    parse_chord_symbol,
)
from music_intelligence.transcribe.notation import NotatedAtomKind, ScoreSpan
from music_intelligence.transcribe.score import ScoreEvent, ScorePart, assemble_score
from music_intelligence.transcribe.spelling import WrittenPitch


def _melody_score():
    events = (
        ScoreEvent(
            event_id="m1",
            part_id="melody",
            staff_id="melody:staff",
            voice_id="v1",
            kind=NotatedAtomKind.NOTE,
            span=ScoreSpan(Fraction(0), Fraction(1)),
            source_event_ids=("src:m1",),
            written_pitch=WrittenPitch("C", 0, 5),
        ),
        ScoreEvent(
            event_id="m2",
            part_id="melody",
            staff_id="melody:staff",
            voice_id="v1",
            kind=NotatedAtomKind.NOTE,
            span=ScoreSpan(Fraction(4), Fraction(1)),
            source_event_ids=("src:m2",),
            written_pitch=WrittenPitch("D", 0, 5),
        ),
    )
    part = ScorePart(
        "melody",
        "Melody",
        "voice",
        ("melody:staff",),
        events,
    )
    return assemble_score(
        score_id="lead:score",
        title="Lead Sheet Source",
        parts=(part,),
    )


def _chart(measures=2):
    items = []
    labels = ("Cmaj7", "Dm7", "G7", "Cmaj7")
    for number in range(1, measures + 1):
        items.append(
            ChartMeasure(
                number=number,
                chords=(
                    ChordChange(
                        Fraction(0),
                        parse_chord_symbol(labels[(number - 1) % len(labels)]),
                    ),
                ),
                section="A" if number == 1 else None,
                repeat_start=number == 1,
                repeat_end=number == measures,
            )
        )
    return ChordChart(
        chart_id="lead:chart",
        title="Lead Sheet Source",
        measures=tuple(items),
    )


def test_output_profile_names_future_score_views_without_merging_reasoners():
    assert OutputProfile.LEAD_SHEET.value == "lead_sheet"
    assert OutputProfile.PIANO_VOCAL.value == "piano_vocal"
    assert OutputProfile.PIANO_REDUCTION.value == "piano_reduction"
    assert OutputProfile.FULL_SCORE.value == "full_score"
    assert OutputProfile.INDIVIDUAL_PART.value == "individual_part"


def test_lead_sheet_projection_combines_melody_with_authoritative_chart():
    projection = project_lead_sheet(
        score=_melody_score(),
        chart=_chart(),
        melody_part_id="melody",
        provenance=("core:form-harmony",),
    )

    assert isinstance(projection, LeadSheetProjection)
    assert projection.melody_part_id == "melody"
    assert projection.chart.measures[0].section == "A"
    assert projection.chart.measures[0].chords[0].chord.display() == "Cmaj7"
    assert "core:form-harmony" in projection.provenance
    assert "transcribe:lead-sheet-projection" in projection.provenance


def test_lead_sheet_rejects_chart_that_does_not_cover_melody():
    with pytest.raises(ValueError, match="does not cover"):
        project_lead_sheet(
            score=_melody_score(),
            chart=_chart(measures=1),
            melody_part_id="melody",
        )


def test_lead_sheet_rejects_meter_mismatch():
    bad_chart = ChordChart(
        chart_id="lead:chart:68",
        title="Lead Sheet Source",
        measures=(
            ChartMeasure(
                number=1,
                chords=(
                    ChordChange(Fraction(0), parse_chord_symbol("Cmaj7")),
                ),
            ),
            ChartMeasure(
                number=2,
                chords=(
                    ChordChange(Fraction(0), parse_chord_symbol("F7")),
                ),
            ),
        ),
        meter_numerator=6,
        meter_denominator=8,
    )
    with pytest.raises(ValueError, match="meter numerator mismatch"):
        project_lead_sheet(
            score=_melody_score(),
            chart=bad_chart,
            melody_part_id="melody",
        )
