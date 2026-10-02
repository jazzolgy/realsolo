from players.bass.written_part_evidence import WrittenPartMeasurementStatus
from players.bass.written_part_measurement import (
    StructuredBassNote,
    measure_written_bass_part,
)


def test_structured_note_events_become_abstract_profile_without_literal_storage_contract():
    notes = (
        StructuredBassNote(36, 0.0, 1.0, 0, frozenset({0,3,7,10}), .96, ("manual:p10",)),
        StructuredBassNote(38, 1.0, .5, 0, frozenset({0,3,7,10}), .95, ("manual:p10",)),
        StructuredBassNote(39, 1.5, .5, 0, frozenset({0,3,7,10}), .94, ("manual:p10",)),
        StructuredBassNote(41, 2.0, 1.0, 5, frozenset({5,9,0,3}), .97, ("manual:p10",)),
    )
    measured = measure_written_bass_part(
        study_id="study.test",
        song_id="score.test",
        source_book_id="scorebook.test",
        source_page=10,
        notes=notes,
    )
    assert measured.status is WrittenPartMeasurementStatus.MEASURED_PROFILE
    assert measured.confidence == .94
    assert measured.profile is not None
    assert measured.profile.event_count == 4
    assert measured.profile.short_subdivision_rate > 0
    assert "players/bass:abstract-written-part-measurement" in measured.provenance


def test_verified_note_events_mark_verified_profile():
    measured = measure_written_bass_part(
        study_id="study.test",
        song_id="score.test",
        source_book_id="scorebook.test",
        source_page=2,
        notes=(StructuredBassNote(36,0.0,1.0,0,frozenset({0,3,7,10})),),
        verified=True,
    )
    assert measured.status is WrittenPartMeasurementStatus.VERIFIED_PROFILE
