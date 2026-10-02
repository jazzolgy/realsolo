from music_intelligence.reasoning.solo_grammar import SoloDevelopmentOperation
from players.drums.solo import (
    SoloDevelopment,
    shared_operation_for_drum_development,
)


def test_drum_specific_developments_map_to_shared_solo_operations():
    assert shared_operation_for_drum_development(SoloDevelopment.REPEAT) is SoloDevelopmentOperation.REPEAT
    assert shared_operation_for_drum_development(SoloDevelopment.ORCHESTRATE) is SoloDevelopmentOperation.REORCHESTRATE
    assert shared_operation_for_drum_development(SoloDevelopment.THREE_BEAT_CYCLE) is SoloDevelopmentOperation.DISPLACE
    assert shared_operation_for_drum_development(SoloDevelopment.METRIC_ILLUSION) is SoloDevelopmentOperation.DISPLACE
    assert shared_operation_for_drum_development(SoloDevelopment.RECAP) is SoloDevelopmentOperation.RECAP
