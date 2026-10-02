from music_intelligence.harmony.jazz_harmony_core import HarmonicAffordance, HarmonicIntent
from music_intelligence.reasoning.legend_style_core import MusicalContextVector
from players.piano import (
    InteractionRole,
    PianoCompingContext,
    PianoCompingEvaluator,
    PianoCompingState,
    PianoVoicingRequest,
    ResolvedHarmonicMaterial,
    build_contextual_comping_candidates,
    expand_candidate_set_rhythmically,
)


def material():
    return ResolvedHarmonicMaterial(
        affordance_id="dominant.altered_color",
        root_pitch_class=7,
        role_pitch_classes={
            "root": (7,),
            "3rd": (11,),
            "b7": (5,),
            "b9": (8,),
            "#9": (10,),
            "b13": (3,),
        },
    )


def affordance():
    return HarmonicAffordance(
        affordance_id="dominant.altered_color",
        intent=HarmonicIntent.INTENSIFY,
        harmonic_role="altered_dominant",
    )


def test_rhythmic_expansion_preserves_silence_and_adds_sounding_variants():
    ctx = PianoCompingContext(
        phrase_boundary_probability=0.9,
        available_space_beats=1.0,
        drummer_activity=0.8,
        section_energy=0.6,
    )
    base = build_contextual_comping_candidates(
        PianoVoicingRequest(material()),
        ctx,
        affordance(),
    )
    expanded = expand_candidate_set_rhythmically(base, ctx)

    assert len(expanded.candidates) > len(base.candidates)
    assert len(expanded.silent) == len(base.silent)


def test_delayed_answer_scores_above_onbeat_answer_in_clear_phrase_space():
    ctx = PianoCompingContext(
        soloist_activity=0.15,
        phrase_boundary_probability=0.95,
        available_space_beats=1.5,
        drummer_activity=0.4,
        ensemble_density=0.25,
        section_energy=0.55,
    )
    base = build_contextual_comping_candidates(
        PianoVoicingRequest(material()),
        ctx,
        affordance(),
    )
    expanded = expand_candidate_set_rhythmically(base, ctx)
    answers = [
        c for c in expanded.candidates
        if c.role is InteractionRole.ANSWER and c.realization is not None
    ]
    delayed = next(c for c in answers if "rhythm:delayed" in c.tags)
    onbeat = next(c for c in answers if "rhythm:on_beat" in c.tags)

    ev = PianoCompingEvaluator()
    delayed_score = ev.evaluate(
        delayed,
        ctx,
        MusicalContextVector(ensemble_activity=0.25),
        PianoCompingState(),
        affordance(),
    )
    onbeat_score = ev.evaluate(
        onbeat,
        ctx,
        MusicalContextVector(ensemble_activity=0.25),
        PianoCompingState(),
        affordance(),
    )
    assert delayed_score.total > onbeat_score.total


def test_active_drums_reward_anticipated_or_offbeat_punctuation():
    ctx = PianoCompingContext(
        soloist_activity=0.3,
        phrase_boundary_probability=0.3,
        available_space_beats=0.0,
        drummer_activity=0.9,
        ensemble_density=0.4,
        section_energy=0.5,
    )
    base = build_contextual_comping_candidates(
        PianoVoicingRequest(material()),
        ctx,
        affordance(),
    )
    expanded = expand_candidate_set_rhythmically(base, ctx)
    punct = [
        c for c in expanded.candidates
        if c.role in {InteractionRole.PUNCTUATE, InteractionRole.ANCHOR}
        and c.realization is not None
    ]
    anticipated = next(c for c in punct if "rhythm:anticipated" in c.tags)
    onbeat = next(c for c in punct if "rhythm:on_beat" in c.tags)

    ev = PianoCompingEvaluator()
    a = ev.evaluate(
        anticipated,
        ctx,
        MusicalContextVector(ensemble_activity=0.4),
        PianoCompingState(),
        affordance(),
    )
    b = ev.evaluate(
        onbeat,
        ctx,
        MusicalContextVector(ensemble_activity=0.4),
        PianoCompingState(),
        affordance(),
    )
    assert a.total > b.total


def test_rhythmic_expansion_never_changes_harmonic_affordance_identity():
    ctx = PianoCompingContext(
        phrase_boundary_probability=0.8,
        available_space_beats=1.0,
        drummer_activity=0.8,
    )
    base = build_contextual_comping_candidates(
        PianoVoicingRequest(material()),
        ctx,
        affordance(),
    )
    expanded = expand_candidate_set_rhythmically(base, ctx)
    assert all(
        c.harmonic_affordance_id == "dominant.altered_color"
        for c in expanded.candidates
    )
