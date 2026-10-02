from fractions import Fraction
import pytest

from music_intelligence.transcribe.notation import NotatedAtomKind, ScoreSpan
from music_intelligence.transcribe.score import (
    ScoreEvent,
    ScorePart,
    ScoreSpanner,
    ScoreSpannerKind,
    assemble_score,
    extract_individual_part,
)
from music_intelligence.transcribe.spelling import WrittenPitch


def _note(event_id, onset):
    return ScoreEvent(
        event_id=event_id,
        part_id="vln",
        staff_id="staff",
        voice_id="v1",
        kind=NotatedAtomKind.NOTE,
        span=ScoreSpan(Fraction(onset), Fraction(1)),
        source_event_ids=(f"src:{event_id}",),
        written_pitch=WrittenPitch("A", 0, 4),
    )


def test_score_accepts_ordered_dynamic_hairpin():
    part = ScorePart(
        "vln", "Violin", "violin", ("staff",),
        (_note("a", 0), _note("b", 2)),
        profile_id="violin",
    )
    spanner = ScoreSpanner(
        "hairpin:1",
        ScoreSpannerKind.CRESCENDO,
        "vln",
        "a",
        "b",
    )

    score = assemble_score(
        score_id="spanner:ok",
        title="Hairpin",
        parts=(part,),
        spanners=(spanner,),
    )

    assert score.spanners == (spanner,)


def test_spanner_rejects_backward_endpoints():
    part = ScorePart(
        "vln", "Violin", "violin", ("staff",),
        (_note("a", 0), _note("b", 2)),
        profile_id="violin",
    )
    spanner = ScoreSpanner(
        "hairpin:bad",
        ScoreSpannerKind.DIMINUENDO,
        "vln",
        "b",
        "a",
    )

    with pytest.raises(ValueError, match="end must follow start"):
        assemble_score(
            score_id="spanner:bad",
            title="Bad",
            parts=(part,),
            spanners=(spanner,),
        )


def test_individual_part_keeps_its_spanners():
    vln = ScorePart(
        "vln", "Violin", "violin", ("staff",),
        (_note("a", 0), _note("b", 2)),
        profile_id="violin",
    )
    spanner = ScoreSpanner(
        "hairpin:1",
        ScoreSpannerKind.CRESCENDO,
        "vln",
        "a",
        "b",
    )
    score = assemble_score(
        score_id="full",
        title="Full",
        parts=(vln,),
        spanners=(spanner,),
    )

    extracted = extract_individual_part(score, "vln")

    assert extracted.spanners == (spanner,)
