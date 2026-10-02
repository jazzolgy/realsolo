from players.drums.calibration import BebopCalibrationTelemetry
from players.drums.model import DrumGesture, DrumHit, DrumVoice, GestureRole, Limb


def test_calibration_telemetry_tracks_restraint_metrics():
    t = BebopCalibrationTelemetry()
    t.observe(DrumGesture(role=GestureRole.SPACE, tags=frozenset({"intentional_non_response"})))
    t.observe(DrumGesture(
        hits=(DrumHit(DrumVoice.SNARE, Limb.LEFT_HAND, 60),),
        role=GestureRole.COMP,
        tags=frozenset({"snare_phrase", "return"}),
    ))
    t.observe(DrumGesture(
        hits=(DrumHit(DrumVoice.BASS_DRUM, Limb.RIGHT_FOOT, 90),),
        role=GestureRole.ACCENT,
        tags=frozenset({"bass_bomb"}),
    ))
    t.observe(DrumGesture(role=GestureRole.SPACE, tags=frozenset({"omit_skip"})))

    snap = t.snapshot()
    assert snap["decisions"] == 4
    assert snap["intentional_non_responses"] == 1
    assert snap["snare_return_share"] == 1.0
    assert snap["bass_bombs"] == 1
    assert snap["ride_skip_omission_share"] == 1.0
