from music_intelligence.reasoning.legend_style_core import CandidateEvent
from music_intelligence.reasoning.solo_grammar import SoloDevelopmentOperation
from players.bass.solo_runtime import BassSoloMemory


def event(pitch=40):
    return CandidateEvent(pitch, .5, source_family="test")


def test_state_streak_does_not_count_as_motif_repetition():
    mem = BassSoloMemory()
    for _ in range(4):
        mem.commit(event(), SoloDevelopmentOperation.STATE)
    assert mem.snapshot().repetition_count == 0


def test_repeat_and_recap_streak_counts_as_motif_repetition():
    mem = BassSoloMemory()
    mem.commit(event(), SoloDevelopmentOperation.STATE)
    mem.commit(event(43), SoloDevelopmentOperation.REPEAT)
    mem.commit(event(45), SoloDevelopmentOperation.RECAP)
    assert mem.snapshot().repetition_count == 2


def test_space_streak_is_tracked_separately_from_motif_repetition():
    mem = BassSoloMemory()
    mem.commit(
        CandidateEvent(None, 1.0, source_family="test_space"),
        SoloDevelopmentOperation.ADD_SPACE,
    )
    mem.commit(
        CandidateEvent(None, 1.0, source_family="test_space"),
        SoloDevelopmentOperation.ADD_SPACE,
    )
    snap = mem.snapshot()
    assert snap.repetition_count == 0
    assert snap.same_operation_count == 2
    assert snap.consecutive_space_count == 2
