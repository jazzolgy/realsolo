from fractions import Fraction

from music_intelligence.transcribe.notation import (
    NotatedAtom,
    NotatedAtomKind,
    NotationCandidate,
    ScoreSpan,
)
from music_intelligence.transcribe.sequence import assemble_monophonic_voice


def candidate(cid, onset, duration):
    return NotationCandidate(
        cid,
        "intent:" + cid,
        atoms=(
            NotatedAtom(
                NotatedAtomKind.NOTE,
                ScoreSpan(Fraction(onset), Fraction(duration)),
                source_event_ids=("src:" + cid,),
            ),
        ),
    )


def test_sequence_inserts_readable_rest_for_gap():
    seq = assemble_monophonic_voice(
        (candidate("a", 0, 1), candidate("b", 2, 1)),
        end=Fraction(4),
    )
    assert [a.kind for a in seq] == [
        NotatedAtomKind.NOTE,
        NotatedAtomKind.REST,
        NotatedAtomKind.NOTE,
        NotatedAtomKind.REST,
    ]
    assert seq[1].span == ScoreSpan(Fraction(1), Fraction(1))


def test_sequence_does_not_hide_voice_overlap():
    try:
        assemble_monophonic_voice(
            (candidate("a", 0, 2), candidate("b", 1, 1)),
        )
    except ValueError as exc:
        assert "overlap" in str(exc)
    else:
        raise AssertionError("monophonic overlap must require voice separation")


def test_swing_like_microtiming_can_prefer_simple_written_eighth_candidate():
    from music_intelligence.reasoning.ensemble_state import CommitmentState
    from music_intelligence.transcribe import (
        CommittedPerformanceEvent,
        PerformedPitch,
        PerformanceTimeSpan,
    )
    from music_intelligence.transcribe.notation import choose_preferred_candidate
    from music_intelligence.transcribe.pipeline import (
        basic_rhythm_candidates,
        notation_intent_from_event,
    )

    event = CommittedPerformanceEvent(
        event_id="swing:offbeat",
        player_id="sax",
        instrument="tenor_sax",
        commitment=CommitmentState.COMMITTED,
        time=PerformanceTimeSpan(
            onset_seconds=1.0,
            offset_seconds=1.2,
            transport_beat=Fraction(2, 3),
            transport_offset_beat=Fraction(1, 1),
        ),
        pitch=PerformedPitch(nominal_midi=67),
    )
    intent = notation_intent_from_event(event)
    preferred = choose_preferred_candidate(basic_rhythm_candidates(event, intent))

    # Exact performed triplet position is available as an alternative, but the
    # readable straight-eighth notation wins under the default complexity cost.
    assert preferred.candidate_id.endswith("eighth")
    assert preferred.atoms[0].span.onset == Fraction(1, 2)
