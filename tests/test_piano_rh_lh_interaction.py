from dataclasses import replace

from players.piano import (
    CompingActionType,
    InteractionRole,
    PianoCompingCandidate,
    PianoCompingContext,
    PianoEnsembleMode,
    PianoVoicingRequest,
    RHLHRelation,
    ResolvedHarmonicMaterial,
    build_contextual_comping_candidates,
    evaluate_rh_lh_interaction,
)
from players.piano.rhythm import apply_rhythmic_intent, PianoRhythmicIntent, RhythmicPlacement


def material():
    return ResolvedHarmonicMaterial(
        affordance_id="test.cmaj",
        root_pitch_class=0,
        role_pitch_classes={
            "root":(0,),
            "3rd":(4,),
            "7th":(11,),
            "9":(2,),
            "13":(9,),
        },
    )


def trio_ctx(**kwargs):
    base=dict(
        ensemble_mode=PianoEnsembleMode.PIANO_SOLO_TRIO,
        piano_foreground_activity=.85,
        piano_foreground_onset_proximity_beats=.05,
        piano_foreground_gap_beats=0.0,
        piano_foreground_rhythm_match_confidence=.1,
    )
    base.update(kwargs)
    return PianoCompingContext(**base)


def sounding_candidate():
    slate=build_contextual_comping_candidates(
        PianoVoicingRequest(material(),duration_beats=.5),
        trio_ctx(piano_foreground_activity=.3),
    )
    return next(
        c for c in slate.sounding
        if "lh_comping" in c.tags
        and c.action_type is CompingActionType.SPARSE_SUPPORT
    )


def test_busy_rh_penalizes_unmotivated_simultaneous_lh_attack():
    c=sounding_candidate()
    result=evaluate_rh_lh_interaction(c,trio_ctx())
    assert result.relation is RHLHRelation.SIMULTANEOUS_SUPPORT
    assert result.components.get("rh_lh_unnecessary_unison_attack",0)<0
    assert result.components.get("rh_lh_weak_doubling_evidence",0)<0


def test_strong_rhythm_match_allows_intentional_doubling():
    c=sounding_candidate()
    result=evaluate_rh_lh_interaction(
        c,
        trio_ctx(piano_foreground_rhythm_match_confidence=.9),
    )
    assert result.relation is RHLHRelation.INTENTIONAL_DOUBLING
    assert result.components.get("rh_lh_intentional_doubling",0)>0


def test_delayed_lh_after_recent_rh_attack_is_rewarded():
    c=sounding_candidate()
    delayed=apply_rhythmic_intent(
        c,
        PianoRhythmicIntent(
            RhythmicPlacement.DELAYED,
            onset_offset_beats=.25,
            duration_scale=.8,
            confidence=.8,
            cell_id="test_delay",
        ),
    )
    result=evaluate_rh_lh_interaction(delayed,trio_ctx())
    assert result.relation is RHLHRelation.DELAYED_RESPONSE
    assert result.components.get("rh_lh_delayed_response",0)>0


def test_phrase_gap_can_invite_lh_answer():
    c=sounding_candidate()
    result=evaluate_rh_lh_interaction(
        c,
        trio_ctx(
            piano_foreground_onset_proximity_beats=.8,
            piano_foreground_gap_beats=1.0,
            piano_foreground_activity=.35,
        ),
    )
    assert result.relation is RHLHRelation.PHRASE_GAP_ANSWER
    assert result.components.get("rh_lh_phrase_gap_answer",0)>0


def test_lh_silence_remains_valid_under_active_rh():
    silence=PianoCompingCandidate(
        action_type=CompingActionType.SILENCE,
        role=InteractionRole.LAY_OUT,
        duration_beats=.5,
        realization=None,
    )
    result=evaluate_rh_lh_interaction(silence,trio_ctx())
    assert result.relation is RHLHRelation.LAY_OUT
    assert result.components.get("rh_lh_busy_lay_out",0)>0
