from music_intelligence.transcribe import (
    CommittedPerformanceEvent,
    ConfidenceBundle,
    ContextCorrection,
    EvidenceRevision,
    PerformedPitch,
    PerformanceCommitment,
    PerformanceTimeSpan,
    ProbabilityEstimate,
    event_from_payload,
    event_to_payload,
)


def test_raw_observation_and_context_posterior_are_preserved_separately():
    event = CommittedPerformanceEvent(
        event_id="bass:beat3",
        player_id="source",
        instrument="unknown",
        commitment=PerformanceCommitment.PLAYED,
        time=PerformanceTimeSpan(1.0, 1.2),
        pitch=PerformedPitch(nominal_midi=43),
        raw_instrument_probabilities=(
            ProbabilityEstimate("bass", .55),
            ProbabilityEstimate("kick_drum", .35),
            ProbabilityEstimate("piano", .10),
        ),
        context_instrument_probabilities=(
            ProbabilityEstimate("bass", .86),
            ProbabilityEstimate("kick_drum", .10),
            ProbabilityEstimate("piano", .04),
        ),
        raw_confidence=ConfidenceBundle(instrument=.55, pitch=.70),
        contextual_confidence=ConfidenceBundle(instrument=.86, pitch=.84),
        context_corrections=(
            ContextCorrection("walking_bass_continuity", "ensemble:recent", .9),
            ContextCorrection("shared_groove_offbeat_match", "groove:swing", .8),
        ),
        revision_history=(
            EvidenceRevision(
                "rev:1",
                "instrument",
                prior_value="bass:0.55",
                revised_value="bass:0.86",
                reason="context posterior",
                source_ref="shared-audio-intelligence",
            ),
        ),
    )
    event.validate()

    assert event.raw_instrument_probabilities[0].probability == .55
    assert event.context_instrument_probabilities[0].probability == .86
    assert event.raw_confidence.instrument == .55
    assert event.contextual_confidence.instrument == .86


def test_observation_posterior_contract_round_trips_without_erasing_raw_values():
    event = CommittedPerformanceEvent(
        event_id="ghost:1",
        player_id="source",
        instrument="upright_bass",
        commitment=PerformanceCommitment.PLAYED,
        time=PerformanceTimeSpan(2.0, 2.08),
        pitch=PerformedPitch(nominal_midi=40),
        raw_role_probabilities=(
            ProbabilityEstimate("bass_attack", .48),
            ProbabilityEstimate("percussive_noise", .42),
            ProbabilityEstimate("unknown", .10),
        ),
        context_role_probabilities=(
            ProbabilityEstimate("bass_ghost_dead_note", .81),
            ProbabilityEstimate("other_percussion", .13),
            ProbabilityEstimate("unknown", .06),
        ),
        context_corrections=(
            ContextCorrection("shared_groove_offbeat_match"),
            ContextCorrection("bass_register_match"),
        ),
    )

    restored = event_from_payload(event_to_payload(event))

    assert restored.raw_role_probabilities == event.raw_role_probabilities
    assert restored.context_role_probabilities == event.context_role_probabilities
    assert restored.context_corrections == event.context_corrections


def test_existing_v1_event_without_new_audio_fields_remains_valid():
    event = CommittedPerformanceEvent(
        event_id="legacy:1",
        player_id="piano",
        instrument="piano",
        commitment=PerformanceCommitment.COMMITTED,
        time=PerformanceTimeSpan(0.0, 0.5),
        pitch=PerformedPitch(nominal_midi=60),
        confidence=ConfidenceBundle(pitch=.9),
    )
    payload = event_to_payload(event)
    restored = event_from_payload(payload)

    assert restored.raw_instrument_probabilities == ()
    assert restored.context_instrument_probabilities == ()
    assert restored.raw_confidence is None
    assert restored.contextual_confidence is None


def test_probability_distribution_cannot_exceed_one():
    event = CommittedPerformanceEvent(
        event_id="bad:distribution",
        player_id="source",
        instrument="unknown",
        commitment=PerformanceCommitment.PLAYED,
        time=PerformanceTimeSpan(0.0, 0.1),
        pitch=PerformedPitch(nominal_midi=60),
        raw_instrument_probabilities=(
            ProbabilityEstimate("bass", .8),
            ProbabilityEstimate("piano", .4),
        ),
    )
    try:
        event.validate()
    except ValueError as exc:
        assert "may not sum above 1" in str(exc)
    else:
        raise AssertionError("invalid probability distribution must fail")
