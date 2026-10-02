from music_intelligence.legends import LegendDomain, VocabularyUseType
from music_intelligence.legends.parker import (
    PARKER_PROFILE_VIEW,
    PARKER_VOCABULARY_INDEX,
)
from players.sax.legend_context import SaxLegendContext, SaxMemoryIntention
from players.sax.physical import SaxPhysicalConstraints, assess_sax_transition


def test_sax_consumes_legend_through_generic_interfaces():
    ctx = SaxLegendContext(PARKER_PROFILE_VIEW, PARKER_VOCABULARY_INDEX)
    tendencies = ctx.tendencies(
        domain=LegendDomain.LINEAR_CONNECTION,
        active_tags=("passing", "neighbor", "close_approach"),
    )
    assert tendencies
    assert ctx.vocabulary(domain=LegendDomain.PHRASE_ENTRANCE) == ()


def test_hybrid_memory_intention_contains_no_future_note_sequence():
    intention = SaxMemoryIntention(
        VocabularyUseType.HYBRID_COMPOSITION,
        active_vocabulary_ids=("CP-FRAG-012", "SELF-MOTIF-008"),
        target="next_harmony_3rd",
        direction="rising",
        interaction_role="ANSWER",
    )
    intention.validate()
    assert not hasattr(intention, "exact_future_notes")


def test_generic_physical_model_is_injected_not_parker_specific():
    c = SaxPhysicalConstraints(
        lowest_playable_midi=50,
        highest_playable_midi=90,
        comfortable_interval_semitones=7,
        max_notes_since_breath=12,
        max_beats_since_breath=8.0,
    )
    a = assess_sax_transition(
        pitch_midi=72,
        previous_pitch_midi=64,
        notes_since_breath=10,
        beats_since_breath=6.5,
        constraints=c,
    )
    assert a.feasible
    assert a.breath_pressure >= 0.8
