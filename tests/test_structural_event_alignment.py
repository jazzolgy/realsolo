from music_intelligence.learning import (
    StructuralAlignmentIndex,
    StructuralAlignmentSpan,
    align_structural_performance_data,
)
from music_intelligence.learning.representation import (
    StructuralPerformanceData,
    StructuralPerformanceEvent,
)
from music_intelligence.learning.score_alignment import (
    MusicalScoreCoordinate,
    PerformancePhase,
)


def test_alignment_sidecar_attaches_coordinate_without_rewriting_event_identity():
    data = StructuralPerformanceData(
        source_id="be_autumn_leaves",
        events=(
            StructuralPerformanceEvent(
                "e1",
                0.0,
                0.5,
                60.0,
                instrument="piano",
                onset_seconds=12.0,
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
                    within_core_form=True,
                ),
                alignment_confidence=0.88,
            ),
        )
    )
    out = align_structural_performance_data(data, index)
    event = out.events[0]
    assert event.event_id == "e1"
    assert event.pitch_midi == 60.0
    assert event.musical_coordinate is not None
    assert event.musical_coordinate.song_id == "autumn_leaves"
    assert 1 <= event.musical_coordinate.form_bar <= 8
    assert out.metadata["structural_alignment_status"] == "structure_aligned"


def test_unmapped_event_remains_navigation_only():
    data = StructuralPerformanceData(
        source_id="unknown",
        events=(
            StructuralPerformanceEvent(
                "e1",
                0.0,
                0.5,
                60.0,
                onset_seconds=5.0,
            ),
        ),
    )
    out = align_structural_performance_data(data, StructuralAlignmentIndex(()))
    assert out.events[0].musical_coordinate is None
    assert out.metadata["structural_alignment_status"] == "navigation_only"
