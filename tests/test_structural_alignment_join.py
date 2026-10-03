from music_intelligence.learning.score_alignment import (
    MusicalScoreCoordinate,
    PerformancePhase,
)
from music_intelligence.learning.structural_join import (
    StructuralAlignmentIndex,
    StructuralAlignmentSpan,
)


def test_structural_join_maps_timestamp_to_form_bar_only_when_range_verified():
    span = StructuralAlignmentSpan(
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
    )
    index = StructuralAlignmentIndex((span,))
    loc = index.locate(source_id="be_autumn_leaves", time_s=12.0)
    assert loc is not None
    assert 1 <= loc.form_bar <= 8
    assert loc.section == "A1"
    assert loc.chorus_index == 0


def test_unmapped_timestamp_stays_unaligned_instead_of_guessing():
    index = StructuralAlignmentIndex(())
    assert index.locate(source_id="unknown", time_s=12.0) is None


def test_section_only_span_does_not_invent_form_bar():
    span = StructuralAlignmentSpan(
        source_id="x",
        start_s=0.0,
        end_s=10.0,
        coordinate=MusicalScoreCoordinate(
            song_id="x",
            section="B",
            performance_phase=PerformancePhase.SOLO,
        ),
    )
    loc = StructuralAlignmentIndex((span,)).locate(source_id="x", time_s=5.0)
    assert loc is not None
    assert loc.form_bar is None
    assert loc.section == "B"
