from music_intelligence.corpus import (
    SEED_SONG_LOCATORS,
    ScoreContextSnapshot,
    ScoreEvidenceKind,
    ScorePosition,
    ScoreSpan,
    StructuredScoreEvidence,
    resolve_score_context,
)
from music_intelligence.harmony.jazz_harmony_core import (
    HarmonicEvidence,
    HarmonicFrame,
    HarmonySource,
)
from music_intelligence.harmony.scale_linear_core import LinearRouteKind
from music_intelligence.legends import LegendDomain, VocabularyMemoryItem, VocabularyUseType
from music_intelligence.legends.parker import PARKER_PROFILE_VIEW
from music_intelligence.legends.parker.vocabulary import ParkerVocabularyIndex
from music_intelligence.reasoning.ensemble_state import InteractionKind
from music_intelligence.reasoning.interaction_scheduler import InteractionDirective

from players.sax.candidates import (
    SaxImmediateContext,
    SaxLegendCandidateContext,
    collect_legend_candidate_material,
    generate_immediate_sax_candidates,
)
from players.sax.interaction import interpret_sax_interaction
from players.sax.legend_context import SaxLegendContext, SaxMemoryIntention
from players.sax.phrase import SaxPhraseContext, SaxPhraseMemory
from players.sax.physical import SaxPhysicalConstraints
from players.sax.policy import choose_sax_runtime_policy
from players.sax.score_context import (
    SaxScoreActivity,
    interpret_score_context,
)


def _song(title):
    return next(x for x in SEED_SONG_LOCATORS if x.title == title)


def _open_solo_snapshot():
    return ScoreContextSnapshot(
        book_id="scorebook.test",
        song_id="score.test",
        position=ScorePosition(page=1, bar=1),
        style=("fast bebop",),
        solo_indication="open solo",
    )


def _frame():
    return HarmonicFrame(
        expected=HarmonicEvidence(
            HarmonySource.EXPECTED,
            symbol="Dm7",
            root_pc=2,
            pitch_classes=frozenset({0, 2, 5, 9}),
            local_key="C",
            function="ii",
        ),
        next_expected=HarmonicEvidence(
            HarmonySource.EXPECTED,
            symbol="G7",
            root_pc=7,
            pitch_classes=frozenset({2, 5, 7, 11}),
            local_key="C",
            function="V7",
        ),
        phrase_position=.5,
        tension=.45,
    )


def test_page_only_feel_change_remains_unresolved_for_sax_policy():
    snap = resolve_score_context(_song("Alfie's Theme"), ScorePosition(page=4, bar=1))
    policy = interpret_score_context(snap)
    assert policy.current_feel is None
    assert policy.pending_feel_change is None
    assert policy.transition_bias == 0


def test_score_style_and_explicit_open_solo_shape_sax_policy():
    policy = interpret_score_context(_open_solo_snapshot())
    assert policy.activity is SaxScoreActivity.OPEN_SOLO
    assert "bebop" in policy.style_tags
    assert policy.density_delta > 0


def test_explicit_score_phrase_boundary_overrides_phrase_maturity_heuristic():
    memory = SaxPhraseMemory()
    decision = memory.decide(SaxPhraseContext(
        pitch_midi=67,
        previous_pitch_midi=65,
        duration_beats=.5,
        beat_in_bar=3.0,
        phrase_maturity=.35,
        score_phrase_boundary_after=True,
    ))
    assert decision.phrase_end
    assert "explicit score phrase-end boundary" in decision.reason


def test_written_head_never_invents_missing_written_note():
    score = interpret_score_context(ScoreContextSnapshot(
        book_id="b",
        song_id="s",
        position=ScorePosition(page=1, bar=1),
        written_melody_active=True,
        written_part_role="head melody",
    ))
    empty = generate_immediate_sax_candidates(
        _frame(),
        SaxImmediateContext(score_policy=score),
    )
    assert empty == ()

    explicit = generate_immediate_sax_candidates(
        _frame(),
        SaxImmediateContext(
            score_policy=score,
            written_pitch_midi=64,
            written_duration_beats=1.0,
        ),
    )
    assert len(explicit) == 1
    assert explicit[0].event.pitch_midi == 64
    assert explicit[0].event.source_family == "score_written"


def test_open_solo_consumes_shared_linear_and_future_harmony_one_event_at_a_time():
    score = interpret_score_context(_open_solo_snapshot())
    out = generate_immediate_sax_candidates(
        _frame(),
        SaxImmediateContext(
            previous_pitch_midi=62,
            local_key_pitch_classes=frozenset({0, 2, 4, 5, 7, 9, 11}),
            score_policy=score,
        ),
    )
    assert out
    assert any(x.route is LinearRouteKind.APPROACH for x in out)
    assert any(x.route is LinearRouteKind.ANTICIPATION for x in out)
    assert all(not hasattr(x, "future_phrase") for x in out)
    assert all(not hasattr(x.event, "exact_future_notes") for x in out)


def test_hold_space_interaction_creates_immediate_rest_candidate():
    score = interpret_score_context(_open_solo_snapshot())
    interaction = interpret_sax_interaction(
        InteractionDirective(
            player_id="sax",
            interaction=InteractionKind.HOLD_SPACE,
            space_priority=.9,
        ),
        score,
    )
    out = generate_immediate_sax_candidates(
        _frame(),
        SaxImmediateContext(
            previous_pitch_midi=62,
            score_policy=score,
            interaction=interaction,
        ),
    )
    assert any(x.event.pitch_midi is None for x in out)


def test_hybrid_parker_memory_biases_generated_event_without_freezing_phrase():
    memory = VocabularyMemoryItem(
        vocabulary_id="CP-FRAG-012",
        source_id="cp-test",
        harmonic_function="ii",
        phrase_position="middle",
        domains=frozenset({LegendDomain.LINEAR_CONNECTION}),
        context_tags=frozenset({"passing"}),
        candidate_uses=frozenset({VocabularyUseType.HYBRID_COMPOSITION}),
        confidence=.9,
    )
    legend = SaxLegendContext(PARKER_PROFILE_VIEW, ParkerVocabularyIndex((memory,)))
    material_ctx = SaxLegendCandidateContext(
        domain=LegendDomain.LINEAR_CONNECTION,
        harmonic_function="ii",
        phrase_position="middle",
        active_tags=("passing",),
        allowed_uses=frozenset({VocabularyUseType.HYBRID_COMPOSITION}),
    )
    materials = collect_legend_candidate_material(legend, material_ctx)
    intention = SaxMemoryIntention(
        VocabularyUseType.HYBRID_COMPOSITION,
        active_vocabulary_ids=("CP-FRAG-012",),
        direction="rising",
    )
    score = interpret_score_context(_open_solo_snapshot())
    out = generate_immediate_sax_candidates(
        _frame(),
        SaxImmediateContext(
            previous_pitch_midi=62,
            local_key_pitch_classes=frozenset({0, 2, 4, 5, 7, 9, 11}),
            score_policy=score,
            legend_materials=materials,
            memory_intention=intention,
        ),
    )
    assert any("CP-FRAG-012" in x.memory_ids for x in out)
    assert any(x.event.source_family == "hybrid_memory" for x in out)


def test_runtime_policy_score_has_priority_over_free_improv_for_written_head():
    snapshot = ScoreContextSnapshot(
        book_id="b",
        song_id="s",
        position=ScorePosition(page=1, bar=1),
        written_melody_active=True,
        written_part_role="head melody",
    )
    decision = choose_sax_runtime_policy(
        snapshot,
        external_allow_improvisation=True,
    )
    assert not decision.allow_improvisation
    assert decision.score.activity is SaxScoreActivity.HEAD_WRITTEN


def test_physical_breath_pressure_can_support_space_without_parker_ownership():
    score = interpret_score_context(_open_solo_snapshot())
    constraints = SaxPhysicalConstraints(
        lowest_playable_midi=50,
        highest_playable_midi=94,
        comfortable_interval_semitones=7,
        max_notes_since_breath=10,
        max_beats_since_breath=8.0,
    )
    out = generate_immediate_sax_candidates(
        _frame(),
        SaxImmediateContext(
            previous_pitch_midi=62,
            score_policy=score,
            notes_since_breath=9,
            beats_since_breath=7.5,
            physical_constraints=constraints,
        ),
    )
    assert any(x.event.pitch_midi is None for x in out)
