from fractions import Fraction
from pathlib import Path

from music_intelligence.reasoning.ensemble_state import CommitmentState
from music_intelligence.transcribe import (
    CommittedPerformanceEvent,
    ConfidenceBundle,
    EvidenceKind,
    EvidenceRef,
    NotatedAtom,
    NotatedAtomKind,
    NotationCandidate,
    NotationIntent,
    PerformanceCommitment,
    PerformedPitch,
    PerformanceTimeSpan,
    ScoreSpan,
    TupletRatio,
    choose_preferred_candidate,
    event_from_payload,
    event_to_payload,
    notation_candidate_from_payload,
    notation_candidate_to_payload,
    notation_intent_from_payload,
    notation_intent_to_payload,
)


def test_performance_evidence_accepts_external_enum_without_importing_it():
    event = CommittedPerformanceEvent(
        event_id="piano:1",
        player_id="piano",
        instrument="piano",
        commitment=CommitmentState.COMMITTED,
        time=PerformanceTimeSpan(1.0, 1.5, transport_beat=4.0),
        pitch=PerformedPitch(nominal_midi=64, cents_offset=-2.0),
        confidence=ConfidenceBundle(pitch=.99, rhythm=.95),
        evidence=(EvidenceRef(EvidenceKind.PLAYER_EVENT, "player:piano:1"),),
    )
    event.validate()
    assert event.duration_seconds == .5


def test_performance_evidence_contract_round_trips_for_standalone_transport():
    original = CommittedPerformanceEvent(
        event_id="audio:7",
        player_id="source",
        instrument="tenor_sax",
        commitment=PerformanceCommitment.PLAYED,
        time=PerformanceTimeSpan(2.0, 2.25),
        pitch=PerformedPitch(frequency_hz=466.16, continuous_pitch_ref="curve:7"),
        articulation=("legato",),
        provenance=("audio-analysis",),
    )
    payload = event_to_payload(original)
    restored = event_from_payload(payload)
    assert payload["schema_version"] == "performance-evidence.v1"
    assert restored.event_id == original.event_id
    assert restored.pitch == original.pitch
    assert restored.articulation == original.articulation


def test_provisional_events_cannot_enter_notation_contract():
    event = CommittedPerformanceEvent(
        event_id="future",
        player_id="bass",
        instrument="upright_bass",
        commitment=CommitmentState.PROVISIONAL,
        time=PerformanceTimeSpan(1.0),
        pitch=PerformedPitch(nominal_midi=40),
    )
    try:
        event.validate()
    except ValueError as exc:
        assert "committed or played" in str(exc)
    else:
        raise AssertionError("provisional events must not enter transcription")


def test_notation_intent_round_trip_preserves_source_identity():
    intent = NotationIntent(
        intent_id="intent:1",
        source_event_ids=("piano:1", "piano:2"),
        gesture_id="gesture:1",
        preserve_as_single_gesture=True,
        confidence=.9,
    )
    restored = notation_intent_from_payload(notation_intent_to_payload(intent))
    assert restored == intent


def test_notation_candidate_round_trip_preserves_exact_score_time():
    candidate = NotationCandidate(
        candidate_id="candidate:1",
        intent_id="intent:1",
        atoms=(
            NotatedAtom(
                kind=NotatedAtomKind.NOTE,
                span=ScoreSpan(Fraction(1, 3), Fraction(2, 3)),
                source_event_ids=("event:1",),
                tuplet=TupletRatio(3, 2),
            ),
        ),
        fidelity_cost=.1,
        readability_cost=.2,
        complexity_cost=.3,
        confidence=.8,
    )
    payload = notation_candidate_to_payload(candidate)
    restored = notation_candidate_from_payload(payload)
    assert restored == candidate
    assert restored.atoms[0].span.onset == Fraction(1, 3)


def test_candidate_selection_prefers_readability_when_total_cost_is_lower():
    literal = NotationCandidate(
        candidate_id="literal",
        intent_id="i",
        atoms=(NotatedAtom(NotatedAtomKind.NOTE, ScoreSpan(Fraction(0), Fraction(7, 32)), ("e",)),),
        fidelity_cost=.01,
        readability_cost=.75,
        complexity_cost=.5,
    )
    readable = NotationCandidate(
        candidate_id="readable",
        intent_id="i",
        atoms=(NotatedAtom(NotatedAtomKind.NOTE, ScoreSpan(Fraction(0), Fraction(1, 4)), ("e",)),),
        fidelity_cost=.12,
        readability_cost=.05,
        complexity_cost=.02,
    )
    assert choose_preferred_candidate((literal, readable)).candidate_id == "readable"


def test_transcribe_contract_layer_has_no_realsolo_runtime_or_player_imports():
    root = Path("src/music_intelligence/transcribe")
    forbidden = (
        "music_intelligence.reasoning",
        "players.",
        "realtime.",
    )
    offenders = []
    for path in root.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        if any(token in text for token in forbidden):
            offenders.append(path.name)
    assert offenders == []
