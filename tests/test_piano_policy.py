import pytest

from music_intelligence.reasoning.legend_style_core import MusicalContextVector
from music_intelligence.reasoning.online_improviser import SoftPlan
from music_intelligence.reasoning.polyphonic_event import (
    PolyphonicEventCandidate,
    VoiceEvent,
)
from players.piano import (
    PianoPerformanceState,
    PianoPolicyEvaluator,
    PianoRealizationCandidate,
    perform_one_piano_action,
)


def voicing(
    pitches,
    *,
    tags=(),
    onsets=None,
    role="comping",
):
    onsets = onsets or [0.0] * len(pitches)
    voices = tuple(
        VoiceEvent(
            voice_id=f"v{i}",
            pitch_midi=pitch,
            onset_offset_beats=onset,
        )
        for i, (pitch, onset) in enumerate(zip(pitches, onsets))
    )
    return PolyphonicEventCandidate(
        voices=voices,
        duration_beats=0.5,
        tags=frozenset(tags),
        role=role,
    )


def test_piano_runtime_commits_one_shared_polyphonic_action():
    state = PianoPerformanceState()
    plan = SoftPlan(
        4,
        "support soloist",
        soft_targets=("clarity",),
        candidate_families=("shell", "rootless"),
    )
    candidate = PianoRealizationCandidate(
        voicing((52, 59, 62), tags=("sparse",)),
        hand_assignment=(("v0", "LH"), ("v1", "RH"), ("v2", "RH")),
    )

    perform_one_piano_action(
        plan,
        PianoPolicyEvaluator(),
        [candidate],
        MusicalContextVector(),
        state,
    )

    assert len(state.committed) == 1
    assert len(state.polyphonic_memory.committed) == 1
    assert state.committed[0].event is state.polyphonic_memory.committed[0]


def test_core_voice_identity_drives_voice_leading_in_piano_policy():
    state = PianoPerformanceState()
    previous = PianoRealizationCandidate(
        PolyphonicEventCandidate(
            voices=(VoiceEvent("low", 48), VoiceEvent("top", 64)),
            duration_beats=1.0,
        )
    )
    state.commit(previous)

    compact = PianoRealizationCandidate(
        PolyphonicEventCandidate(
            voices=(VoiceEvent("low", 50), VoiceEvent("top", 65)),
            duration_beats=1.0,
        )
    )
    displaced = PianoRealizationCandidate(
        PolyphonicEventCandidate(
            voices=(VoiceEvent("low", 60), VoiceEvent("top", 76)),
            duration_beats=1.0,
        )
    )

    evaluator = PianoPolicyEvaluator()
    context = MusicalContextVector()
    assert evaluator.evaluate(compact, context, state).total > evaluator.evaluate(
        displaced, context, state
    ).total


def test_staggered_voice_onsets_remain_one_piano_gesture():
    candidate = PianoRealizationCandidate(
        voicing(
            (48, 55, 59, 64),
            onsets=(-0.015, 0.0, 0.01, 0.025),
        )
    )
    candidate.validate()

    assert candidate.event.voice_onset_spread_beats == pytest.approx(0.04)
    assert [v.pitch_midi for v in candidate.event.voices_by_onset] == [48, 55, 59, 64]


def test_piano_range_is_local_not_core():
    candidate = PianoRealizationCandidate(
        PolyphonicEventCandidate(
            voices=(VoiceEvent("low", 10),),
            duration_beats=0.5,
        )
    )
    with pytest.raises(ValueError):
        candidate.validate()


def test_hand_assignment_is_piano_specific():
    candidate = PianoRealizationCandidate(
        voicing((48, 60, 67)),
        hand_assignment=(("v0", "LH"), ("v1", "RH"), ("v2", "RH")),
    )
    candidate.validate()
    assert dict(candidate.hand_assignment)["v0"] == "LH"


def test_dense_sustain_is_penalized_when_ensemble_is_busy():
    evaluator = PianoPolicyEvaluator()
    state = PianoPerformanceState()
    context = MusicalContextVector(ensemble_activity=0.9)

    dry = PianoRealizationCandidate(
        voicing((48, 55, 59, 64, 69), tags=("dense",)),
        pedal="none",
    )
    sustained = PianoRealizationCandidate(
        voicing((48, 55, 59, 64, 69), tags=("dense",)),
        pedal="sustain",
    )

    assert evaluator.evaluate(dry, context, state).total > evaluator.evaluate(
        sustained, context, state
    ).total


def test_future_note_freezing_is_still_rejected():
    plan = SoftPlan(8, "build tension", exact_future_notes=(60, 64, 67))
    candidate = PianoRealizationCandidate(voicing((60, 64, 67)))

    with pytest.raises(ValueError):
        perform_one_piano_action(
            plan,
            PianoPolicyEvaluator(),
            [candidate],
            MusicalContextVector(),
            PianoPerformanceState(),
        )
