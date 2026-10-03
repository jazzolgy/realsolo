"""Generate a two-bar polyphonic piano MusicXML example.

Run:
    python examples/transcription_polyphonic_piano_2bar.py
"""
from pathlib import Path

from music_intelligence.transcribe import (
    CommittedPerformanceEvent,
    NotationEngine,
    PartTranscriptionRequest,
    PerformanceTimeSpan,
    PerformedPitch,
)
from music_intelligence.transcribe.allocation import StaffProfile
from music_intelligence.transcribe.events import PerformanceCommitment


def event(event_id, beat, duration, midi, role):
    return CommittedPerformanceEvent(
        event_id=event_id,
        player_id="piano",
        instrument="piano",
        commitment=PerformanceCommitment.PLAYED,
        time=PerformanceTimeSpan(
            onset_seconds=beat * .5,
            offset_seconds=(beat + duration) * .5,
            transport_beat=beat,
            transport_offset_beat=beat + duration,
        ),
        pitch=PerformedPitch(nominal_midi=float(midi)),
        voice_role=role,
        dynamic=.5,
        provenance=("example:polyphonic-piano",),
    )


def main() -> Path:
    engine = NotationEngine()
    request = PartTranscriptionRequest(
        part_id="pn",
        name="Piano",
        instrument="piano",
        events=(
            event("mel:1", .5, 1.5, 72, "melody"),
            event("mel:2", 2, 1, 76, "melody"),
            event("mel:3", 4, 1, 79, "melody"),
            event("mel:4", 5, 1, 77, "melody"),
            event("inner:1", 1, 1, 64, "inner"),
            event("inner:2", 2, 1, 67, "inner"),
            event("bass:1", 0, 2, 48, "bass"),
            event("bass:2", 2, 2, 43, "bass"),
            event("bass:3", 4, 2, 45, "bass"),
            event("bass:4", 6, 2, 43, "bass"),
        ),
        staffs=(
            StaffProfile(
                "pn:upper",
                "upper",
                role_tags=frozenset({"melody", "inner"}),
                nominal_low_midi=60,
                nominal_high_midi=108,
            ),
            StaffProfile(
                "pn:lower",
                "lower",
                role_tags=frozenset({"bass"}),
                nominal_low_midi=21,
                nominal_high_midi=60,
            ),
        ),
        end_beat=8.0,
        infer_piano_gestures=False,
        infer_dynamic_hairpins=False,
    )
    _, xml = engine.transcribe_take_musicxml(
        (request,),
        score_id="example:piano:2bar",
        title="Polyphonic Piano Example",
    )
    target = Path("polyphonic_piano_2bar.musicxml")
    target.write_text(xml, encoding="utf-8")
    print(target)
    return target


if __name__ == "__main__":
    main()
