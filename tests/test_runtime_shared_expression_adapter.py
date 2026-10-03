from music_intelligence.expression import ExpressiveIntent
from realtime.ensemble_app.player_contract import (
    RenderGesture,
    RenderVoice,
    apply_shared_expression_to_render_gesture,
)


def test_shared_expression_changes_how_not_what():
    gesture=RenderGesture(
        role="piano",
        voices=(RenderVoice(60,70,.5,instrument_role="piano"),),
    )
    intent=ExpressiveIntent(
        dynamic_level=.8,
        accent_strength=.7,
        note_body=.75,
        foreground_weight=.3,
        perceptual_intensity=.7,
        confidence=.9,
    )
    out=apply_shared_expression_to_render_gesture(gesture,intent)
    assert out.voices[0].pitch_midi==60
    assert out.voices[0].velocity!=70
    assert out.voices[0].duration_beats!=.5
    assert out.annotations["shared_expression"]=="1"
