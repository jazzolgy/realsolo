from players.bass.partial_written_part_profile import (
    BassFeatureMeasurement,
    PartialBassLineProfile,
    compare_partial_bass_profiles,
)
from players.bass.written_part_comparator import BassLineAbstractProfile


def generated():
    return BassLineAbstractProfile(
        event_count=16,
        root_occupancy_rate=.25,
        structural_occupancy_rate=.75,
        scalar_motion_rate=.50,
        chromatic_approach_rate=.20,
        enclosure_rate=.05,
        repeated_pitch_rate=.10,
        direction_reversal_rate=.35,
        offbeat_onset_rate=.30,
        short_subdivision_rate=.40,
        quarter_floor_coverage=.90,
        register_center=40.0,
        register_span=12,
        register_slope=.1,
    )


def test_partial_profile_compares_only_measured_features():
    ref = PartialBassLineProfile(
        event_count=None,
        measurements=(
            BassFeatureMeasurement("offbeat_onset_rate", .25, .95, ("vision:p10",)),
            BassFeatureMeasurement("short_subdivision_rate", .45, .90, ("vision:p10",)),
        ),
    )
    cmp = compare_partial_bass_profiles(ref, generated())
    assert cmp.compared_features == ("offbeat_onset_rate", "short_subdivision_rate")
    assert 0.0 <= cmp.weighted_distance <= 1.0


def test_partial_profile_rejects_duplicate_feature_measurement():
    ref = PartialBassLineProfile(
        measurements=(
            BassFeatureMeasurement("offbeat_onset_rate", .2, .9),
            BassFeatureMeasurement("offbeat_onset_rate", .3, .8),
        ),
    )
    try:
        ref.validate()
    except ValueError as exc:
        assert "duplicate" in str(exc)
    else:
        raise AssertionError("expected duplicate feature rejection")
