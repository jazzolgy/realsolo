from fractions import Fraction

from music_intelligence.transcribe.notation import NotatedAtomKind, ScoreSpan
from music_intelligence.transcribe.quality import (
    QualityIssueSeverity,
    audit_score_for_performance,
)
from music_intelligence.transcribe.score import ScoreEvent, ScorePart, assemble_score
from music_intelligence.transcribe.spelling import WrittenPitch


def note(eid, part_id, staff_id, voice, pitch):
    return ScoreEvent(
        event_id=eid,
        part_id=part_id,
        staff_id=staff_id,
        voice_id=voice,
        kind=NotatedAtomKind.NOTE,
        span=ScoreSpan(Fraction(0), Fraction(1)),
        source_event_ids=("src:" + eid,),
        written_pitch=pitch,
    )


def test_quality_audit_flags_classical_staff_count_mismatch():
    event = note("p:1", "piano", "upper", "v1", WrittenPitch("C", 0, 5))
    part = ScorePart(
        "piano",
        "Piano",
        "piano",
        ("upper",),
        (event,),
        profile_id="piano",
    )
    score = assemble_score(score_id="quality:staff", title="Bad Piano", parts=(part,))

    report = audit_score_for_performance(score)

    assert report.has_errors
    assert any(i.code == "staff-count-mismatch" for i in report.issues)


def test_quality_audit_warns_on_advisory_instrument_range():
    event = note("vln:1", "vln", "staff", "v1", WrittenPitch("C", 0, 2))
    part = ScorePart(
        "vln",
        "Violin",
        "violin",
        ("staff",),
        (event,),
        profile_id="violin",
    )
    score = assemble_score(score_id="quality:range", title="Range", parts=(part,))

    report = audit_score_for_performance(score)

    issue = next(i for i in report.issues if i.code == "written-range")
    assert issue.severity is QualityIssueSeverity.WARNING
    assert issue.event_id == "vln:1"
    assert not report.has_errors


def test_generic_instrument_profile_is_informational_not_failure():
    event = note("x:1", "x", "staff", "v1", WrittenPitch("C", 0, 4))
    part = ScorePart("x", "Unknown", "future_instrument", ("staff",), (event,))
    score = assemble_score(score_id="quality:generic", title="Generic", parts=(part,))

    report = audit_score_for_performance(score)

    assert not report.has_errors
    assert not report.needs_review
    assert any(i.code == "instrument-profile-missing" for i in report.issues)
