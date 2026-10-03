"""Generate the transcription 8-bar golden MusicXML example.

Run:
    python examples/transcription_golden_8bar.py
"""
from pathlib import Path

from music_intelligence.reasoning.ensemble_state import CommitmentState
from music_intelligence.transcribe import (
    CommittedPerformanceEvent,
    NotationEngine,
    PartTranscriptionRequest,
    PerformedPitch,
    PerformanceTimeSpan,
    ScoreKeySignature,
)
from music_intelligence.transcribe.allocation import StaffProfile


def event(event_id, beat, midi, dynamic, phrase):
    return CommittedPerformanceEvent(
        event_id=event_id,
        player_id="flute",
        instrument="flute",
        commitment=CommitmentState.PLAYED,
        time=PerformanceTimeSpan(
            onset_seconds=beat * .5,
            offset_seconds=beat * .5 + .46,
            transport_beat=beat,
            transport_offset_beat=beat + .9,
        ),
        pitch=PerformedPitch(nominal_midi=float(midi)),
        dynamic=dynamic,
        phrase_context_id=phrase,
        provenance=("example:golden-performance-evidence",),
    )


def main() -> Path:
    engine = NotationEngine()
    request = PartTranscriptionRequest(
        part_id="fl",
        name="Flute",
        instrument="flute",
        events=(
            event("a1", 0, 72, .30, "A"),
            event("a2", 1, 74, .36, "A"),
            event("a3", 2, 76, .43, "A"),
            event("a4", 3, 77, .52, "A"),
            event("a5", 4, 79, .54, "A"),
            event("a6", 6, 81, .56, "A"),
            event("b1", 16, 81, .72, "B"),
            event("b2", 17, 79, .66, "B"),
            event("b3", 18, 77, .59, "B"),
            event("b4", 19, 76, .51, "B"),
            event("b5", 20, 74, .46, "B"),
            event("b6", 22, 72, .40, "B"),
        ),
        staffs=(StaffProfile("fl:staff", "fl"),),
        end_beat=32.0,
    )
    _, xml = engine.transcribe_take_musicxml(
        (request,),
        score_id="golden:8bar",
        title="Golden 8-Bar Phrase",
        key_signature=ScoreKeySignature(0, "major"),
    )
    target = Path("golden_8bar.musicxml")
    target.write_text(xml, encoding="utf-8")
    print(target)
    return target


if __name__ == "__main__":
    main()
