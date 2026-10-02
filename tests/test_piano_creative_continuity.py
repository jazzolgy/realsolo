from dataclasses import replace

from music_intelligence.harmony.jazz_harmony_core import HarmonicEvidence, HarmonicFrame, HarmonySource
from music_intelligence.reasoning.polyphonic_event import PolyphonicEventCandidate, VoiceEvent
from players.piano import (
    CompingActionType,
    CreativityContext,
    DimensionContinuityProfile,
    HarmonicContinuityFeatures,
    InteractionRole,
    PianoCompingCandidate,
    PianoCompingContext,
    PianoCompingEvaluator,
    PianoCompingState,
    PianoRealizationCandidate,
    evaluate_creative_continuity,
    profile_from_harmonic_context,
)


def sounding_candidate(tags=frozenset({"rhythm:on_beat","register:stay","dynamic:medium","touch:neutral"})):
    event=PolyphonicEventCandidate(
        voices=(VoiceEvent("v1",52),VoiceEvent("v2",64)),
        duration_beats=0.5,
        tags=frozenset({"shell","sparse"}),
        role="comping",
        source_family="piano_shell",
    )
    return PianoCompingCandidate(
        action_type=CompingActionType.SPARSE_SUPPORT,
        role=InteractionRole.SUPPORT,
        duration_beats=0.5,
        realization=PianoRealizationCandidate(event),
        tags=tags,
    )


def vamp_features(boundary=0.0):
    return HarmonicContinuityFeatures(
        hold_stability=0.1,
        change_rate=1.0,
        recurrence_strength=0.95,
        boundary_pressure=boundary,
        pattern_consistency_strength=0.8 if boundary < 0.5 else 0.25,
    )


def test_vamp_profile_preserves_rhythm_more_than_expression_axes():
    profile=profile_from_harmonic_context(vamp_features())
    assert profile.rhythm > profile.register
    assert profile.rhythm > profile.dynamic
    assert profile.rhythm > profile.touch


def test_phrase_boundary_loosens_structural_continuity():
    stable=profile_from_harmonic_context(vamp_features(boundary=0.0))
    boundary=profile_from_harmonic_context(vamp_features(boundary=0.9))
    assert boundary.rhythm < stable.rhythm
    assert boundary.family < stable.family
    assert boundary.role < stable.role


def test_exact_repeat_gets_creative_stagnation_penalty():
    original=sounding_candidate()
    previous=__import__("players.piano",fromlist=["GestureSignature"]).GestureSignature.from_candidate(original)
    score=evaluate_creative_continuity(
        original,
        previous,
        DimensionContinuityProfile(),
        CreativityContext(creativity_strength=1.0),
    )
    assert score.components.get("creative_stagnation",0)<0


def test_change_in_free_expression_axis_can_create_coherent_novelty():
    original=sounding_candidate()
    previous=__import__("players.piano",fromlist=["GestureSignature"]).GestureSignature.from_candidate(original)
    changed=replace(
        original,
        tags=frozenset({"rhythm:on_beat","register:higher","dynamic:soft","touch:neutral"}),
    )
    profile=DimensionContinuityProfile(
        role=0.9,
        family=0.9,
        rhythm=0.9,
        register=0.15,
        dynamic=0.15,
        touch=0.2,
    )
    score=evaluate_creative_continuity(
        changed,
        previous,
        profile,
        CreativityContext(creativity_strength=1.0,coherence_floor=0.3),
    )
    assert score.components.get("creative_change:register",0)>0
    assert score.components.get("creative_change:dynamic",0)>0
    assert score.components.get("coherent_novelty",0)>0


def test_changing_every_high_continuity_anchor_can_lose_coherence():
    original=sounding_candidate()
    previous=__import__("players.piano",fromlist=["GestureSignature"]).GestureSignature.from_candidate(original)
    changed=replace(
        original,
        role=InteractionRole.BUILD,
        tags=frozenset({"rhythm:offbeat","register:higher","dynamic:strong","touch:percussive"}),
    )
    new_event=replace(
        changed.realization.event,
        source_family="piano_quartal",
    )
    changed=replace(
        changed,
        realization=replace(changed.realization,event=new_event),
    )
    profile=DimensionContinuityProfile(
        role=0.95,
        family=0.95,
        rhythm=0.95,
        register=0.8,
        dynamic=0.8,
        touch=0.8,
    )
    score=evaluate_creative_continuity(
        changed,
        previous,
        profile,
        CreativityContext(creativity_strength=1.0,coherence_floor=0.7),
    )
    assert score.components.get("coherence_loss",0)<0


def test_creativity_can_exist_even_in_high_consistency_context():
    original=sounding_candidate()
    previous=__import__("players.piano",fromlist=["GestureSignature"]).GestureSignature.from_candidate(original)
    changed=replace(
        original,
        tags=frozenset({"rhythm:on_beat","register:stay","dynamic:soft","touch:legato"}),
    )
    profile=profile_from_harmonic_context(vamp_features())
    score=evaluate_creative_continuity(
        changed,
        previous,
        profile,
        CreativityContext(creativity_strength=0.8,coherence_floor=0.3),
    )
    assert score.total>0


def test_creativity_context_zero_disables_novelty_reward():
    original=sounding_candidate()
    previous=__import__("players.piano",fromlist=["GestureSignature"]).GestureSignature.from_candidate(original)
    changed=replace(
        original,
        tags=frozenset({"rhythm:on_beat","register:higher","dynamic:soft","touch:neutral"}),
    )
    score=evaluate_creative_continuity(
        changed,
        previous,
        DimensionContinuityProfile(),
        CreativityContext(creativity_strength=0.0),
    )
    assert score.total==0.0


def test_comping_evaluator_includes_creative_continuity_component():
    state=PianoCompingState()
    original=sounding_candidate()
    state.commit(original,section_energy=0.5)
    state.last_harmonic_continuity=vamp_features()

    changed=replace(
        original,
        tags=frozenset({"rhythm:on_beat","register:higher","dynamic:soft","touch:neutral"}),
    )
    ctx=PianoCompingContext(creativity_strength=1.0)
    score=PianoCompingEvaluator().evaluate(
        changed,
        ctx,
        __import__("music_intelligence.reasoning.legend_style_core",fromlist=["MusicalContextVector"]).MusicalContextVector(),
        state,
    )
    assert any(k.startswith("creative_continuity:") for k in score.components)


def test_creativity_layer_stores_no_future_solution():
    profile=profile_from_harmonic_context(vamp_features())
    assert not hasattr(profile,"future_voicings")
    assert not hasattr(profile,"next_rhythm")
    assert not hasattr(profile,"planned_sequence")
