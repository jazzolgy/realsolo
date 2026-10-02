from players.drums.chorus_memory import BebopChorusMemory, chorus_gesture_adjustment
from players.drums.model import DrumGesture, DrumHit, DrumVoice, GestureRole, Limb


def test_dense_recent_chorus_history_rewards_space_and_penalizes_activity():
    memory = BebopChorusMemory(recent_8bar_density=0.85, need_to_back_off=True)
    space = DrumGesture(role=GestureRole.SPACE)
    comp = DrumGesture(
        hits=(DrumHit(DrumVoice.SNARE, Limb.LEFT_HAND, 60),),
        role=GestureRole.COMP,
    )
    s, _ = chorus_gesture_adjustment(space, memory)
    c, _ = chorus_gesture_adjustment(comp, memory)
    assert s > 0
    assert c < 0


def test_approaching_boundary_prefers_setup_without_forcing_future_fill():
    memory = BebopChorusMemory(next_form_boundary_distance_bars=1.0)
    setup = DrumGesture(
        hits=(DrumHit(DrumVoice.SNARE, Limb.LEFT_HAND, 70),),
        role=GestureRole.SETUP,
    )
    score, _ = chorus_gesture_adjustment(setup, memory)
    assert score > 0
    assert not hasattr(memory, "future_fill")
