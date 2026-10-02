from music_intelligence.reasoning.intro import EntryAction, EntryDecision
from music_intelligence.reasoning.ensemble_state import InteractionKind
from players.piano.intro_realizer import realize_piano_intro_entry
from players.bass.intro_realizer import realize_bass_intro_entry
from players.sax.intro_realizer import realize_sax_intro_entry
from players.drums.intro_realizer import realize_drum_intro_entry

def decision(action):
    return EntryDecision(action=action,readiness=.8,permission=.8,confidence=.8)

def test_wait_means_space_for_every_player():
    for fn in (realize_piano_intro_entry,realize_bass_intro_entry,realize_drums:=realize_drum_intro_entry):
        plan=fn("p",decision(EntryAction.WAIT))
        assert plan.intent.interaction is InteractionKind.HOLD_SPACE
        assert plan.intent.density==0.
    sax=realize_sax_intro_entry("s",decision(EntryAction.WAIT))
    assert sax.intent.interaction is InteractionKind.HOLD_SPACE

def test_drums_do_not_jump_from_shadow_to_full_groove():
    plan=realize_drum_intro_entry("d",decision(EntryAction.SHADOW))
    assert plan.realization_hint!="full_groove_entry"
    assert plan.intent.density<.2

def test_bass_light_support_is_sparse():
    plan=realize_bass_intro_entry("b",decision(EntryAction.LIGHT_SUPPORT))
    assert "single_root" in plan.realization_hint
    assert plan.intent.space_request>.5

def test_sax_head_leader_can_keep_leadership_on_entry():
    plan=realize_sax_intro_entry("s",decision(EntryAction.FULL_JOIN),is_head_leader=True)
    assert plan.intent.interaction is InteractionKind.LEAD
    assert plan.intent.leadership>.8

def test_piano_partial_join_is_not_full_comping():
    plan=realize_piano_intro_entry("p",decision(EntryAction.PARTIAL_JOIN))
    assert plan.realization_hint=="rhythmic_comping_entry"
    assert plan.intent.density<.5
