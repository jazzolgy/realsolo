from fractions import Fraction

from music_intelligence.transcribe.notation import (
    NotatedAtom,
    NotatedAtomKind,
    NotationCandidate,
    NotationIntent,
    NotationRelevance,
    ScoreSpan,
    choose_preferred_candidate,
)


def test_notation_intent_preserves_sources_and_interpretation_context():
    intent = NotationIntent(
        intent_id="intent:piano:g1",
        source_event_ids=("piano:g1:n1", "piano:g1:n2"),
        relevance=NotationRelevance.INCLUDE,
        gesture_id="piano:g1",
        preserve_as_single_gesture=True,
        confidence=.91,
        alternatives=("spread_chord", "simultaneous_chord"),
        evidence_ids=("player:piano:g1",),
        provenance=("transcribe:intent:v1",),
    )
    intent.validate()
    assert intent.preserve_as_single_gesture
    assert len(intent.alternatives) == 2


def test_candidate_is_rhythm_only_before_pitch_spelling_and_staff_allocation():
    candidate = NotationCandidate(
        candidate_id="cand:1",
        intent_id="intent:1",
        atoms=(
            NotatedAtom(
                NotatedAtomKind.NOTE,
                ScoreSpan(Fraction(0), Fraction(1, 2)),
                source_event_ids=("event:1",),
            ),
        ),
        fidelity_cost=.1,
        readability_cost=.05,
    )
    candidate.validate()

    atom = candidate.atoms[0]
    assert not hasattr(atom, "written_pitch")
    assert not hasattr(atom, "staff")
    assert not hasattr(atom, "voice_number")


def test_preferred_candidate_balances_fidelity_and_readability_without_deleting_alternatives():
    literal = NotationCandidate(
        "literal",
        "intent:1",
        atoms=(
            NotatedAtom(
                NotatedAtomKind.NOTE,
                ScoreSpan(Fraction(0), Fraction(7, 32)),
                source_event_ids=("event:1",),
            ),
        ),
        fidelity_cost=.01,
        readability_cost=.75,
        complexity_cost=.5,
        confidence=.9,
    )
    readable = NotationCandidate(
        "readable",
        "intent:1",
        atoms=(
            NotatedAtom(
                NotatedAtomKind.NOTE,
                ScoreSpan(Fraction(0), Fraction(1, 4)),
                source_event_ids=("event:1",),
            ),
        ),
        fidelity_cost=.12,
        readability_cost=.05,
        complexity_cost=.02,
        confidence=.82,
    )
    assert choose_preferred_candidate((literal, readable)).candidate_id == "readable"


def test_omission_is_an_explicit_notation_intent_not_data_loss():
    intent = NotationIntent(
        intent_id="intent:pedal-resonance",
        source_event_ids=("audio:resonance:9",),
        relevance=NotationRelevance.OMIT,
        confidence=.84,
        evidence_ids=("audio:segment:9",),
    )
    intent.validate()
    assert intent.relevance is NotationRelevance.OMIT
