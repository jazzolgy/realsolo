from music_intelligence.learning import (
    MusicalScoreCoordinate,
    PerformancePhase,
    StructuralPerformanceData,
    StructuralPerformanceEvent,
)
from music_intelligence.learning.structural_join import (
    StructuralAlignmentIndex,
    StructuralAlignmentSpan,
    align_structural_performance_data,
)


def test_timestamp_sidecar_attaches_canonical_position():
    data = StructuralPerformanceData(
        source_id="be_autumn_leaves",
        events=(
            StructuralPerformanceEvent(
                "e1", 0.0, 0.5, 60.0,
                instrument="piano",
                audio_onset_s=12.0,
                audio_offset_s=12.2,
            ),
        ),
    )
    index = StructuralAlignmentIndex(
        (
            StructuralAlignmentSpan(
                source_id="be_autumn_leaves",
                start_s=8.0,
                end_s=17.5,
                start_form_bar=1,
                end_form_bar=8,
                coordinate=MusicalScoreCoordinate(
                    song_id="autumn_leaves",
                    section="A1",
                    form_length_bars=32,
                    chorus_index=0,
                    performance_phase=PerformancePhase.HEAD,
                    arrangement_segment="core_form",
                    within_core_form=True,
                ),
                alignment_confidence=0.88,
            ),
        )
    )
    aligned = align_structural_performance_data(data, index)
    event = aligned.events[0]
    assert event.musical_position is not None
    assert event.musical_position.song_id == "autumn_leaves"
    assert 1 <= event.musical_position.form_bar <= 8
    assert event.canonical_position_key is not None
    assert aligned.metadata["structural_alignment_status"] == "structure_aligned"


def test_missing_alignment_is_not_guessed():
    data = StructuralPerformanceData(
        source_id="unknown",
        events=(
            StructuralPerformanceEvent(
                "e1", 0.0, 0.5, 60.0,
                audio_onset_s=5.0,
            ),
        ),
    )
    aligned = align_structural_performance_data(data, StructuralAlignmentIndex(()))
    assert aligned.events[0].musical_position is None
    assert aligned.metadata["structural_alignment_status"] == "navigation_only"
