from music_intelligence.harmony.harmonic_time import (
    CadenceStrength,
    HarmonicSpan,
    KeyRegionStrength,
    TonicizationEvidence,
    infer_local_key,
    key_of_the_moment_score,
    summarize_harmonic_rhythm,
)


def test_harmonic_rhythm_summary_detects_faster_changes():
    slow = summarize_harmonic_rhythm((
        HarmonicSpan("a", 0, 4),
        HarmonicSpan("b", 4, 4),
    ))
    fast = summarize_harmonic_rhythm((
        HarmonicSpan("a", 0, 1),
        HarmonicSpan("b", 1, 1),
        HarmonicSpan("c", 2, 1),
        HarmonicSpan("d", 3, 1),
    ))
    assert fast.changes_per_4_beats > slow.changes_per_4_beats


def test_harmonic_rhythm_acceleration_is_temporal_not_tonal():
    a = summarize_harmonic_rhythm((
        HarmonicSpan("a", 0, 4),
        HarmonicSpan("b", 4, 2),
        HarmonicSpan("c", 6, 1),
    ))
    assert a.acceleration > 0


def test_secondary_dominant_resolution_can_remain_tonicization():
    h = infer_local_key(TonicizationEvidence(
        tonic_pc=2,
        dominant_root_pc=9,
        resolves_to_target=True,
        target_duration_beats=2,
        target_repetitions=1,
        cadence_strength=CadenceStrength.WEAK,
        section_boundary_alignment=.0,
        return_to_parent_key=.9,
    ))
    assert h.strength in {KeyRegionStrength.TONICIZATION, KeyRegionStrength.TRANSIENT}


def test_sustained_cadential_region_can_become_local_key():
    h = infer_local_key(TonicizationEvidence(
        tonic_pc=7,
        dominant_root_pc=2,
        has_predominant=True,
        resolves_to_target=True,
        target_duration_beats=12,
        target_repetitions=3,
        cadence_strength=CadenceStrength.STRONG,
        section_boundary_alignment=.55,
        return_to_parent_key=.1,
    ))
    assert h.strength is KeyRegionStrength.LOCAL
    assert key_of_the_moment_score(h) > .6


def test_section_boundary_can_promote_key_region_strength():
    h = infer_local_key(TonicizationEvidence(
        tonic_pc=5,
        dominant_root_pc=0,
        has_predominant=True,
        resolves_to_target=True,
        target_duration_beats=16,
        target_repetitions=4,
        cadence_strength=CadenceStrength.STRONG,
        section_boundary_alignment=.9,
    ))
    assert h.strength is KeyRegionStrength.SECTIONAL


def test_harmonic_time_contains_no_fixed_future_chord_sequence():
    h = infer_local_key(TonicizationEvidence(tonic_pc=0))
    assert not hasattr(h, "future_chords")
    assert not hasattr(h, "future_notes")
