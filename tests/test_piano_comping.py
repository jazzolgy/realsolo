import pytest

from music_intelligence.harmony.jazz_harmony_core import (
    HarmonicAffordance,
    HarmonicIntent,
)
from music_intelligence.reasoning.legend_style_core import MusicalContextVector
from music_intelligence.reasoning.online_improviser import SoftPlan
from music_intelligence.reasoning.polyphonic_event import (
    PolyphonicEventCandidate,
    VoiceEvent,
)
from players.piano import (
    CompingActionType,
    InteractionRole,
    PianoCompingCandidate,
    PianoCompingContext,
    PianoCompingEvaluator,
    PianoCompingState,
    PianoRealizationCandidate,
    perform_one_comping_action,
)


def realization(pitches=(52, 59, 62), tags=("sparse",)):
    return PianoRealizationCandidate(
        PolyphonicEventCandidate(
            voices=tuple(
                VoiceEvent(f"v{i}", pitch)
                for i, pitch in enumerate(pitches)
            ),
            duration_beats=0.5,
            tags=frozenset(tags),
            role="comping",
        )
    )


def silence(role=InteractionRole.LAY_OUT):
    return PianoCompingCandidate(
        action_type=CompingActionType.SILENCE,
        role=role,
        duration_beats=0.5,
    )


def sounding(
    *,
    action=CompingActionType.SPARSE_SUPPORT,
    role=InteractionRole.SUPPORT,
    pitches=(52, 59, 62),
    tags=("sparse",),
    affordance_id=None,
    duration=0.5,
):
    return PianoCompingCandidate(
        action_type=action,
        role=role,
        duration_beats=duration,
        realization=realization(pitches, tags),
        harmonic_affordance_id=affordance_id,
    )


def test_silence_is_first_class_and_does_not_create_fake_polyphonic_event():
    state = PianoCompingState()
    result = perform_one_comping_action(
        SoftPlan(2, "yield"),
        PianoCompingEvaluator(),
        [silence()],
        PianoCompingContext(soloist_activity=0.9, ensemble_density=0.8),
        MusicalContextVector(ensemble_activity=0.9),
        state,
    )
    assert result.candidate.action_type is CompingActionType.SILENCE
    assert len(state.committed) == 1
    assert len(state.piano.polyphonic_memory.committed) == 0


def test_busy_solo_prefers_silence_over_dense_support():
    evaluator = PianoCompingEvaluator()
    state = PianoCompingState()
    ctx = PianoCompingContext(
        soloist_activity=0.9,
        phrase_boundary_probability=0.1,
        ensemble_density=0.85,
        recent_piano_density=0.8,
    )
    musical = MusicalContextVector(ensemble_activity=0.9)
    candidates = [
        silence(),
        sounding(
            pitches=(45, 52, 59, 62, 66),
            tags=("dense",),
            role=InteractionRole.SUPPORT,
        ),
    ]
    chosen = evaluator.choose_immediate(candidates, ctx, musical, state)
    assert chosen.candidate.action_type is CompingActionType.SILENCE


def test_phrase_space_prefers_answer_over_silence_when_solo_releases():
    evaluator = PianoCompingEvaluator()
    state = PianoCompingState()
    ctx = PianoCompingContext(
        soloist_activity=0.2,
        phrase_boundary_probability=0.9,
        available_space_beats=1.0,
        ensemble_density=0.35,
    )
    musical = MusicalContextVector(ensemble_activity=0.35)
    candidates = [
        silence(role=InteractionRole.ANSWER),
        sounding(
            action=CompingActionType.RESPONSE,
            role=InteractionRole.ANSWER,
            tags=("sparse",),
        ),
    ]
    chosen = evaluator.choose_immediate(candidates, ctx, musical, state)
    assert chosen.candidate.action_type is CompingActionType.RESPONSE


def test_same_harmony_can_produce_different_action_from_context():
    evaluator = PianoCompingEvaluator()
    musical = MusicalContextVector(chord_symbol="G7", ensemble_activity=0.5)
    candidates = [
        silence(),
        sounding(
            action=CompingActionType.RESPONSE,
            role=InteractionRole.ANSWER,
            tags=("sparse",),
        ),
    ]

    busy = evaluator.choose_immediate(
        candidates,
        PianoCompingContext(
            soloist_activity=0.95,
            phrase_boundary_probability=0.1,
            ensemble_density=0.8,
        ),
        musical,
        PianoCompingState(),
    )
    open_space = evaluator.choose_immediate(
        candidates,
        PianoCompingContext(
            soloist_activity=0.15,
            phrase_boundary_probability=0.9,
            available_space_beats=1.0,
            ensemble_density=0.25,
        ),
        musical,
        PianoCompingState(),
    )

    assert busy.candidate.action_type is CompingActionType.SILENCE
    assert open_space.candidate.action_type is CompingActionType.RESPONSE


def test_piano_consumes_core_affordance_without_rebuilding_harmony():
    affordance = HarmonicAffordance(
        affordance_id="dominant.altered_color",
        intent=HarmonicIntent.INTENSIFY,
        harmonic_role="altered_dominant",
    )
    evaluator = PianoCompingEvaluator()
    ctx = PianoCompingContext()
    musical = MusicalContextVector(chord_symbol="G7")

    aligned = sounding(
        affordance_id="dominant.altered_color",
        role=InteractionRole.SUPPORT,
    )
    mismatched = sounding(
        affordance_id="major7.color_field",
        role=InteractionRole.SUPPORT,
    )

    a = evaluator.evaluate(aligned, ctx, musical, PianoCompingState(), affordance)
    b = evaluator.evaluate(mismatched, ctx, musical, PianoCompingState(), affordance)
    assert a.total > b.total


def test_future_note_freezing_remains_forbidden():
    with pytest.raises(ValueError):
        perform_one_comping_action(
            SoftPlan(4, "build", exact_future_notes=(60, 64, 67)),
            PianoCompingEvaluator(),
            [silence()],
            PianoCompingContext(),
            MusicalContextVector(),
            PianoCompingState(),
        )
