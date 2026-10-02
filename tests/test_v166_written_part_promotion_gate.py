from players.bass.written_part_comparator import BassLineAbstractProfile
from players.bass.written_part_evidence import (
    MeasuredWrittenPartEvidence,
    WrittenPartMeasurementStatus,
    promote_written_part_prior,
)


def profile():
    return BassLineAbstractProfile(
        event_count=16,
        root_occupancy_rate=.25,
        structural_occupancy_rate=.75,
        scalar_motion_rate=.50,
        chromatic_approach_rate=.20,
        enclosure_rate=.05,
        repeated_pitch_rate=.10,
        direction_reversal_rate=.35,
        offbeat_onset_rate=.15,
        short_subdivision_rate=.20,
        quarter_floor_coverage=.95,
        register_center=40.0,
        register_span=12,
        register_slope=.1,
    )


def test_qualitative_observation_cannot_become_runtime_prior():
    ev = MeasuredWrittenPartEvidence(
        "study.asa",
        "score.newreal2.asa",
        "scorebook.newreal.2",
        10,
        WrittenPartMeasurementStatus.QUALITATIVE_ONLY,
        .99,
        None,
        ("vision-reviewed",),
    )
    assert promote_written_part_prior(ev) is None


def test_measured_profile_can_be_promoted_when_confident():
    ev = MeasuredWrittenPartEvidence(
        "study.asa",
        "score.newreal2.asa",
        "scorebook.newreal.2",
        10,
        WrittenPartMeasurementStatus.MEASURED_PROFILE,
        .95,
        profile(),
        ("structured-note-events",),
    )
    prior = promote_written_part_prior(ev)
    assert prior is not None
    assert prior.scalar_preference == .50


def test_low_confidence_measurement_stays_out_of_runtime():
    ev = MeasuredWrittenPartEvidence(
        "study.actual-proof",
        "score.newreal3.actual_proof",
        "scorebook.newreal.3",
        2,
        WrittenPartMeasurementStatus.MEASURED_PROFILE,
        .70,
        profile(),
    )
    assert promote_written_part_prior(ev) is None
