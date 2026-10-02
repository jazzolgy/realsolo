from music_intelligence.reasoning.legend_style_core import CandidateEvent, MusicalContextVector
from players.piano import (
    HeadInterpretationContext,
    PianoSoloContext,
    PianoSoloEvaluator,
    RHSwingContext,
    SwingRole,
    apply_rh_swing,
    interpret_head_event,
    swing_ratio_for_tempo,
)


def test_130_bpm_rh_eighth_is_swung_not_straight():
    event=CandidateEvent(72,.5,tags=frozenset({"connector"}))
    swung=apply_rh_swing(
        event,
        RHSwingContext(
            tempo_bpm=130,
            role=SwingRole.SOLO,
            subdivision_phase=.5,
        ),
    )
    assert swung.onset_offset_beats > .15
    assert "swing_offbeat" in swung.tags
    # Swing ratio is now owned by Shared GrooveTemporalContext.
    assert 2.0 < swing_ratio_for_tempo(130) < 2.3


def test_faster_swing_is_less_exaggerated_than_slow_swing():
    assert swing_ratio_for_tempo(100) > swing_ratio_for_tempo(180)


def test_head_interpreter_changes_timing_without_changing_pitch():
    written=CandidateEvent(
        69,
        1.0,
        tags=frozenset({"harmonic_identity","guide_tone"}),
    )
    out=interpret_head_event(
        written,
        HeadInterpretationContext(
            tempo_bpm=130,
            subdivision_phase=.5,
            phrase_end_pressure=.8,
            next_harmony_known=True,
            bass_activity=.8,
            drummer_activity=.8,
        ),
    )
    assert out.pitch_midi == written.pitch_midi
    assert out.duration_beats > written.duration_beats
    assert "head_phrase_elasticity" in out.tags
    assert "head_vocal_ending" in out.tags


def test_accessible_parker_connector_beats_undirected_large_leap():
    evaluator=PianoSoloEvaluator()
    context=PianoSoloContext(
        musical=MusicalContextVector(
            phrase_maturity=.5,
            recent_altered_density=.2,
        ),
        previous_pitch_midi=60,
    )
    close=CandidateEvent(
        62,.25,
        tags=frozenset({"connector","passing","directed_target"}),
    )
    leap=CandidateEvent(
        72,.25,
        tags=frozenset({"color_tone"}),
    )
    a=evaluator.evaluate(close,context)
    b=evaluator.evaluate(leap,context)
    assert a.total > b.total
    assert a.components.get("accessible_bebop_motion",0)>0
    assert b.components.get("undirected_large_leap",0)<0


def test_directed_large_leap_remains_possible():
    evaluator=PianoSoloEvaluator()
    context=PianoSoloContext(
        musical=MusicalContextVector(),
        previous_pitch_midi=60,
    )
    target=CandidateEvent(
        69,.5,
        tags=frozenset({"guide_tone","directed_target","resolution_path"}),
    )
    result=evaluator.evaluate(target,context)
    assert result.components.get("directed_large_leap",0)>0
