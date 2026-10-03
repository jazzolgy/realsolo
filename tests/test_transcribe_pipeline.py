from fractions import Fraction

from music_intelligence.reasoning.ensemble_state import CommitmentState
from music_intelligence.transcribe import (
    CommittedPerformanceEvent,
    ConfidenceBundle,
    PerformedPitch,
    PerformanceTimeSpan,
)
from music_intelligence.transcribe.notation import (
    NotationRelevance,
    choose_preferred_candidate,
)
from music_intelligence.transcribe.pipeline import (
    basic_rhythm_candidates,
    notation_intent_from_event,
)


def make_event(onset=1.02, offset=1.49):
    return CommittedPerformanceEvent(
        event_id="piano:evt:1",
        player_id="piano",
        instrument="piano",
        commitment=CommitmentState.COMMITTED,
        time=PerformanceTimeSpan(
            onset_seconds=10.0,
            offset_seconds=10.45,
            transport_beat=onset,
            transport_offset_beat=offset,
        ),
        pitch=PerformedPitch(nominal_midi=64),
        gesture_id="piano:g1",
        articulation=("legato",),
        confidence=ConfidenceBundle(
            rhythm=.94,
            notation_relevance=.91,
        ),
        provenance=("player/piano",),
    )


def test_event_projects_to_notation_intent_without_score_decisions():
    event = make_event()
    intent = notation_intent_from_event(event)
    assert intent.source_event_ids == (event.event_id,)
    assert intent.gesture_id == "piano:g1"
    assert intent.articulation_intent == ("legato",)
    assert not hasattr(intent, "written_pitch")
    assert not hasattr(intent, "staff")


def test_basic_candidate_family_preserves_alternatives_and_prefers_readable_fit():
    event = make_event()
    intent = notation_intent_from_event(event)
    candidates = basic_rhythm_candidates(event, intent)

    assert {c.candidate_id.rsplit(":", 1)[-1] for c in candidates} >= {
        "quarter",
        "eighth",
        "sixteenth",
    }
    preferred = choose_preferred_candidate(candidates)
    assert preferred.atoms[0].span.onset == Fraction(1)
    assert preferred.atoms[0].span.duration == Fraction(1, 2)


def test_omit_intent_produces_no_notation_candidates():
    event = make_event()
    intent = notation_intent_from_event(
        event,
        relevance=NotationRelevance.OMIT,
    )
    assert basic_rhythm_candidates(event, intent) == ()


def test_triplet_candidate_is_available_without_forcing_it_as_preferred():
    event = make_event(onset=Fraction(4, 3), offset=Fraction(5, 3))
    intent = notation_intent_from_event(event)
    candidates = basic_rhythm_candidates(event, intent)
    triplets = [c for c in candidates if c.candidate_id.endswith("triplet-eighth")]
    assert len(triplets) == 1
    assert triplets[0].atoms[0].tuplet is not None
    assert triplets[0].atoms[0].tuplet.actual == 3


# Contract note: score-facing dynamics should prefer the source-normalized
# perceptual ordinal over legacy amplitude-like dynamic values.
