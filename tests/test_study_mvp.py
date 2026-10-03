from music_intelligence.learning.score_alignment import PerformancePhase
from music_intelligence.study.session import (
    ManualFormClock,
    SectionRange,
    artifacts_for_window,
)
from music_intelligence.study.audio import AudioWindowFeatures


def test_manual_form_clock_emits_canonical_musical_score_coordinate():
    clock=ManualFormClock(
        song_id="Autumn Leaves",
        bpm=206.7,
        meter_numerator=4,
        meter_denominator=4,
        form_length_bars=32,
        form_start_s=8.0,
        sections=(
            SectionRange("A1",1,8),
            SectionRange("A2",9,16),
            SectionRange("B",17,24),
            SectionRange("C",25,32),
        ),
        performance_phase=PerformancePhase.HEAD,
    )
    p=clock.coordinate_at(8.0)
    assert p is not None
    assert p.song_id == "Autumn Leaves"
    assert p.bar == 1
    assert p.form_bar == 1
    assert p.beat == 1.0
    assert p.section == "A1"
    assert p.chorus_index == 0


def test_manual_form_clock_wraps_form_and_keeps_chorus_index():
    clock=ManualFormClock(
        song_id="Test",
        bpm=120,
        form_length_bars=4,
        form_start_s=0,
    )
    # 4/4 @ 120 bpm -> 2 seconds per bar. 8.5 s is chorus 2, bar 1, beat 2.
    p=clock.coordinate_at(8.5)
    assert p is not None
    assert p.chorus_index == 1
    assert p.form_bar == 1
    assert 1.9 < p.beat < 2.1


def test_study_artifacts_are_navigation_only_without_alignment():
    window=AudioWindowFeatures(
        start_s=10.0,end_s=12.0,rms=.03,peak=.2,
        zero_crossing_rate=.05,spectral_centroid_hz=1200.0,
        onset_rate_hz=3.0,activity=.25,
    )
    artifacts=artifacts_for_window("source",window,None)
    assert len(artifacts)==2
    assert all(a.musical_position is None for a in artifacts)
    assert {a.domain.value for a in artifacts} == {"rhythm_groove","expression"}


def test_study_artifacts_use_canonical_coordinate_when_aligned():
    window=AudioWindowFeatures(
        start_s=10.0,end_s=12.0,rms=.03,peak=.2,
        zero_crossing_rate=.05,spectral_centroid_hz=1200.0,
        onset_rate_hz=3.0,activity=.25,
    )
    clock=ManualFormClock(song_id="Test",bpm=120,form_length_bars=4)
    coordinate=clock.coordinate_at(2.0)
    artifacts=artifacts_for_window("source",window,coordinate)
    assert all(a.musical_position is coordinate for a in artifacts)
    assert artifacts[0].musical_position.form_bar == 2
