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
