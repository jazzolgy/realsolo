from music_intelligence.reasoning.polyphonic_event import (
    InstrumentAssignment,
    PolyphonicEventCandidate,
    VoiceEvent,
)

from realtime.ensemble_app.player_adapter import (
    committed_polyphonic_to_render_gesture,
)


def test_committed_piano_event_projects_without_redeciding_music():
    event = PolyphonicEventCandidate(
        voices=(
            VoiceEvent(
                "lh",
                50,
                onset_offset_beats=0.0,
                duration_beats=0.6,
                velocity=62,
                assignment=InstrumentAssignment(instrument_family="piano"),
            ),
            VoiceEvent(
                "rh",
                65,
                onset_offset_beats=0.04,
                duration_beats=0.5,
                velocity=74,
                articulation=("accent",),
                assignment=InstrumentAssignment(instrument_family="piano"),
            ),
        ),
        duration_beats=0.75,
        onset_offset_beats=0.1,
        velocity=70,
        source_family="piano_rootless",
        tags=frozenset({"support", "rootless"}),
    )

    gesture = committed_polyphonic_to_render_gesture(
        event,
        player_role="piano",
    )

    assert gesture.source == "piano_rootless"
    assert [v.pitch_midi for v in gesture.voices] == [50, 65]
    assert gesture.voices[1].onset_offset_beats == 0.14
    assert gesture.voices[1].articulation == ("accent",)


def test_drum_assignment_routes_to_drum_hits():
    event = PolyphonicEventCandidate(
        voices=(
            VoiceEvent(
                "ride",
                51,
                velocity=64,
                assignment=InstrumentAssignment(instrument_family="drums"),
            ),
        ),
        duration_beats=0.25,
        role="drum_gesture",
    )
    gesture = committed_polyphonic_to_render_gesture(event, player_role="drums")
    assert not gesture.voices
    assert len(gesture.drum_hits) == 1
    assert gesture.drum_hits[0].pitch_midi == 51


def test_player_status_is_explicit_about_fallback_boundary():
    from realtime.ensemble_app.player_provider import current_stage1_provider_status

    states = {x.role: x.to_dict() for x in current_stage1_provider_status()}
    assert states["piano"]["source"] == "player/piano"
    assert states["bass"]["source"] == "player/bass"
    assert states["drums"]["source"] == "player/drums"
