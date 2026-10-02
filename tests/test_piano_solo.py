import pytest

from music_intelligence.reasoning.legend_style_core import (
    CandidateEvent,
    MusicalContextVector,
)
from music_intelligence.reasoning.online_improviser import SoftPlan
from players.piano import (
    PianoSoloContext,
    PianoSoloEvaluator,
    PianoSoloState,
    default_bebop_legend_blend,
    perform_one_piano_solo_event,
)


def test_default_piano_solo_uses_parker_as_first_bebop_prior():
    blend = default_bebop_legend_blend()
    assert blend.profiles
    profile, weight = blend.profiles[0]
    assert "charlie_parker" in profile.profile_id
    assert profile.era_or_school == "bebop"
    assert weight == 1.0


def test_close_approach_gets_bebop_support():
    evaluator = PianoSoloEvaluator()
    context = PianoSoloContext(
        musical=MusicalContextVector(
            phrase_maturity=0.4,
        )
    )
    plain = CandidateEvent(63, 0.5, tags=frozenset({"chord_tone"}))
    approach = CandidateEvent(
        63,
        0.5,
        tags=frozenset({"close_approach", "directed_target"}),
    )
    assert evaluator.evaluate(approach, context).total > evaluator.evaluate(plain, context).total


def test_directed_altered_color_beats_undirected_altered_color():
    evaluator = PianoSoloEvaluator()
    context = PianoSoloContext(
        musical=MusicalContextVector(
            phrase_maturity=0.5,
            recent_chord_identity_strength=0.5,
            recent_altered_density=0.3,
        )
    )
    undirected = CandidateEvent(70, 0.5, tags=frozenset({"altered"}))
    directed = CandidateEvent(
        70,
        0.5,
        tags=frozenset({"altered", "directed_target", "resolution_path"}),
    )
    assert evaluator.evaluate(directed, context).total > evaluator.evaluate(undirected, context).total


def test_piano_range_is_instrument_local():
    evaluator = PianoSoloEvaluator()
    context = PianoSoloContext(right_hand_low_midi=48, right_hand_high_midi=84)
    inside = CandidateEvent(72, 0.5, tags=frozenset({"passing"}))
    outside_preferred = CandidateEvent(96, 0.5, tags=frozenset({"passing"}))
    assert evaluator.evaluate(inside, context).total > evaluator.evaluate(outside_preferred, context).total


def test_busy_left_hand_redirects_solo_toward_space_without_disabling_solo():
    evaluator = PianoSoloEvaluator()
    context = PianoSoloContext(
        left_hand_comping_activity=0.9,
        ensemble_density=0.8,
    )
    rest = CandidateEvent(None, 0.5, tags=frozenset({"rest"}))
    dense_run = CandidateEvent(72, 0.25, tags=frozenset({"dense_run"}))
    rest_score = evaluator.evaluate(rest, context)
    run_score = evaluator.evaluate(dense_run, context)
    assert rest_score.components.get("texture_space", 0) > 0
    assert run_score.components.get("texture_crowding", 0) < 0


def test_one_event_commit_contract_is_preserved():
    evaluator = PianoSoloEvaluator()
    state = PianoSoloState()
    context = PianoSoloContext()
    candidates = (
        CandidateEvent(60, 0.5, tags=frozenset({"chord_tone"})),
        CandidateEvent(61, 0.5, tags=frozenset({"close_approach"})),
    )

    chosen = perform_one_piano_solo_event(
        SoftPlan(2.0, "bebop line"),
        evaluator,
        candidates,
        context,
        state,
    )
    assert len(state.memory.committed) == 1
    assert state.memory.committed[0] == chosen.candidate


def test_exact_future_solo_notes_are_still_forbidden():
    evaluator = PianoSoloEvaluator()
    state = PianoSoloState()
    with pytest.raises(ValueError):
        perform_one_piano_solo_event(
            SoftPlan(
                4.0,
                "bebop phrase",
                exact_future_notes=(60, 62, 64, 65),
            ),
            evaluator,
            (CandidateEvent(60, 0.5),),
            PianoSoloContext(),
            state,
        )


def test_sparse_left_hand_allows_right_hand_to_clarify_harmony():
    evaluator = PianoSoloEvaluator()
    ctx = PianoSoloContext(
        left_hand_harmonic_coverage=0.1,
    )
    harmonic = CandidateEvent(
        67,
        0.5,
        tags=frozenset({"guide_tone", "harmonic_identity"}),
    )
    score = evaluator.evaluate(harmonic, ctx)
    assert score.components.get("right_hand_harmonic_support", 0) > 0


def test_dense_left_hand_can_penalize_duplicate_right_hand_harmonic_outline():
    evaluator = PianoSoloEvaluator()
    ctx = PianoSoloContext(
        left_hand_harmonic_coverage=0.9,
    )
    duplicate = CandidateEvent(
        67,
        0.5,
        tags=frozenset({"harmonic_outline"}),
    )
    score = evaluator.evaluate(duplicate, ctx)
    assert score.components.get("duplicate_harmonic_outline", 0) < 0


def test_active_left_hand_register_can_penalize_right_hand_collision():
    evaluator = PianoSoloEvaluator()
    ctx = PianoSoloContext(
        left_hand_comping_activity=0.8,
        left_hand_register_top_midi=64,
    )
    near = CandidateEvent(67, 0.5, tags=frozenset({"passing"}))
    score = evaluator.evaluate(near, ctx)
    assert score.components.get("left_hand_register_collision", 0) < 0


def test_busy_left_hand_rhythm_can_penalize_dense_right_hand_run():
    evaluator = PianoSoloEvaluator()
    ctx = PianoSoloContext(
        left_hand_rhythmic_coverage=0.9,
    )
    run = CandidateEvent(
        72,
        0.25,
        tags=frozenset({"dense_run"}),
    )
    score = evaluator.evaluate(run, ctx)
    assert score.components.get("left_hand_rhythmic_crowding", 0) < 0
