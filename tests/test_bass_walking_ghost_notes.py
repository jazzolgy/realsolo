from music_intelligence.reasoning.groove_context import GrooveFeel, build_groove_context
from music_intelligence.reasoning.legend_style_core import CandidateEvent
from players.bass.ghost_notes import (
    BassGhostContext,
    choose_walking_ghost_note,
    commit_walking_ghost,
)
from players.bass.performance_memory import (
    BassArticulation,
    BassCommittedAction,
    BassPerformanceMemory,
)


def _swing():
    return build_groove_context(
        GrooveFeel.SWING,
        tempo_bpm=120.0,
        grammar_id="swing.eighth_triplet_feel",
        subdivision_hint="swing_eighth",
    )


def _memory_with_pitch(pitch=40):
    memory=BassPerformanceMemory()
    memory.commit(BassCommittedAction(
        CandidateEvent(pitch,1.0,tags=frozenset({"bass","walking"})),
        articulation=BassArticulation.NEUTRAL,
        harmonic_role="root",
        metric_role="continuation",
    ))
    return memory


def test_walking_can_choose_percussive_eighth_ghost_on_shared_swing_offbeat():
    groove=_swing()
    memory=_memory_with_pitch()
    beat=1.0+groove.swing_offbeat_fraction
    decision=choose_walking_ghost_note(BassGhostContext(
        mode="walking",
        beat_in_measure=beat,
        tempo_bpm=120.0,
        groove=groove,
        memory=memory.snapshot(),
        ensemble_activity=.35,
        opportunity_hint=.45,
    ))
    assert decision.play
    assert decision.rhythmic_value_beats == .5
    assert decision.sounding_duration_beats < .25
    assert decision.velocity < 50
    assert decision.articulation in {BassArticulation.GHOSTED,BassArticulation.DEAD}
    assert decision.physical_pitch_midi == 40


def test_ghost_commit_does_not_change_walking_pitch_contour():
    groove=_swing()
    memory=_memory_with_pitch(43)
    before=memory.snapshot()
    decision=choose_walking_ghost_note(BassGhostContext(
        mode="walking",
        beat_in_measure=1.0+groove.swing_offbeat_fraction,
        groove=groove,
        memory=before,
        ensemble_activity=.30,
        opportunity_hint=.6,
    ))
    assert decision.play
    commit_walking_ghost(memory,decision)
    after=memory.snapshot()
    assert after.previous_pitch_midi == 43
    assert after.recent_pitches == before.recent_pitches
    assert after.recent_ghost_count == 1


def test_ghosts_are_not_inserted_on_quarter_note_anchor():
    groove=_swing()
    decision=choose_walking_ghost_note(BassGhostContext(
        mode="walking",
        beat_in_measure=2.0,
        groove=groove,
        memory=_memory_with_pitch().snapshot(),
        ensemble_activity=.25,
        opportunity_hint=1.0,
    ))
    assert not decision.play


def test_ghosts_do_not_leak_into_nonwalking_mode():
    groove=_swing()
    decision=choose_walking_ghost_note(BassGhostContext(
        mode="solo",
        beat_in_measure=1.0+groove.swing_offbeat_fraction,
        groove=groove,
        memory=_memory_with_pitch().snapshot(),
        ensemble_activity=.25,
        opportunity_hint=1.0,
    ))
    assert not decision.play


def test_recent_ghosts_create_density_restraint():
    groove=_swing()
    memory=_memory_with_pitch()
    beat=1.0+groove.swing_offbeat_fraction
    first=choose_walking_ghost_note(BassGhostContext(
        mode="walking",beat_in_measure=beat,groove=groove,
        memory=memory.snapshot(),ensemble_activity=.35,opportunity_hint=.45,
    ))
    assert first.play
    commit_walking_ghost(memory,first)

    second=choose_walking_ghost_note(BassGhostContext(
        mode="walking",beat_in_measure=beat,groove=groove,
        memory=memory.snapshot(),ensemble_activity=.35,opportunity_hint=.45,
    ))
    if second.play:
        commit_walking_ghost(memory,second)

    third=choose_walking_ghost_note(BassGhostContext(
        mode="walking",beat_in_measure=beat,groove=groove,
        memory=memory.snapshot(),ensemble_activity=.35,opportunity_hint=.45,
    ))
    assert third.score < first.score
    assert not third.play
