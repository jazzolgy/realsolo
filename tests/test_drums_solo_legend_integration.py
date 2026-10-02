from music_intelligence.legends import (
    LegendDomain,
    LegendProfileView,
    VocabularyMemoryItem,
    VocabularyUseType,
)
from music_intelligence.reasoning.legend_style_core import LegendProfile, StyleTendency
from players.drums.legend_adapter import (
    DrumLegendFeature,
    drum_vocabulary_intent,
    project_legend_views,
)
from players.drums.model import DrummerRuntimeContext
from players.drums.solo import (
    DrumSoloPlan,
    DrumSoloState,
    SoloArc,
    SoloDevelopment,
    build_solo_candidates,
)


def motif_legend():
    profile = LegendProfile(
        profile_id="drummer.example",
        display_name="Example",
        instrument_family="drums",
        era_or_school="jazz",
        tendencies=(
            StyleTendency(
                "motif",
                DrumLegendFeature.MOTIF_DEVELOPMENT.value,
                weight=0.9,
                confidence=1.0,
            ),
            StyleTendency(
                "orchestration",
                DrumLegendFeature.ORCHESTRATION_MOBILITY.value,
                weight=0.8,
                confidence=1.0,
            ),
        ),
    )
    view = LegendProfileView(
        legend_id="drummer.example",
        profile=profile,
        domain_features={
            LegendDomain.MOTIF_DEVELOPMENT: (
                DrumLegendFeature.MOTIF_DEVELOPMENT.value,
            ),
            LegendDomain.ARTICULATION: (
                DrumLegendFeature.ORCHESTRATION_MOBILITY.value,
            ),
        },
    )
    return project_legend_views(((view, 1.0),))


def hybrid_memory():
    item = VocabularyMemoryItem(
        vocabulary_id="DR-MOTIF-X",
        source_id="recording.example",
        rhythm="motif displaced",
        articulation="orchestrated motif",
        candidate_uses=frozenset({VocabularyUseType.HYBRID_COMPOSITION}),
        confidence=1.0,
        provenance=("shared_legend",),
    )
    return drum_vocabulary_intent(item, use_type=VocabularyUseType.HYBRID_COMPOSITION)


def score_for(candidates, development):
    return next(c.score for c in candidates if c.development is development)


def test_legend_motif_prior_changes_solo_candidate_score():
    plan = DrumSoloPlan(arc=SoloArc.DEVELOP, adventurousness=0.6)
    context = DrummerRuntimeContext(position_in_bar_beats=1.0, phrase_position=0.5)
    state = DrumSoloState(gestures_committed=3, statements=3)

    plain = build_solo_candidates(plan, context, state)
    styled = build_solo_candidates(plan, context, state, legend=motif_legend())

    assert score_for(styled, SoloDevelopment.DISPLACE) > score_for(
        plain, SoloDevelopment.DISPLACE
    )


def test_hybrid_memory_affects_current_solo_development_only():
    plan = DrumSoloPlan(arc=SoloArc.DEVELOP, adventurousness=0.6)
    context = DrummerRuntimeContext(position_in_bar_beats=1.0, phrase_position=0.5)
    state = DrumSoloState(gestures_committed=3, statements=3)
    intent = hybrid_memory()

    plain = build_solo_candidates(plan, context, state)
    remembered = build_solo_candidates(
        plan, context, state, vocabulary_intents=(intent,)
    )

    assert max(c.score for c in remembered) >= max(c.score for c in plain)
    assert not hasattr(intent, "future_hits")
    assert not hasattr(intent, "future_phrase")


def test_recap_and_resolve_orchestration_branch_is_explicit():
    plan = DrumSoloPlan(
        arc=SoloArc.REENTRY,
        adventurousness=0.6,
        target_reentry=True,
    )
    context = DrummerRuntimeContext(
        position_in_bar_beats=3.0,
        phrase_position=0.95,
        section_transition=True,
    )
    state = DrumSoloState(gestures_committed=6, statements=6)

    candidates = build_solo_candidates(plan, context, state)
    recap = next(c for c in candidates if c.development is SoloDevelopment.RECAP)
    resolve = next(c for c in candidates if c.development is SoloDevelopment.RESOLVE)
    assert recap.gesture.hits
    assert resolve.gesture.hits
