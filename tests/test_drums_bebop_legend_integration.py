from music_intelligence.legends import LegendDomain, LegendProfileView
from music_intelligence.reasoning.legend_style_core import LegendProfile, StyleTendency
from players.drums.bebop import BebopPhraseMemory, SoloistEnergyProjection
from players.drums.bebop_runtime import (
    BebopRuntimeProjection,
    build_bebop_candidates,
    score_bebop_gesture,
)
from players.drums.legend_adapter import (
    DrumLegendFeature,
    project_legend_views,
)
from players.drums.model import DrummerRuntimeContext, DrummerSoftPlan, DrumVoice


def ride_legend_projection():
    profile = LegendProfile(
        profile_id="drummer.example",
        display_name="Example",
        instrument_family="drums",
        era_or_school="bebop",
        tendencies=(
            StyleTendency(
                "ride",
                DrumLegendFeature.RIDE_SURFACE_FLEXIBILITY.value,
                context_tags=frozenset({"fast_bebop"}),
                weight=0.8,
                confidence=1.0,
            ),
        ),
    )
    view = LegendProfileView(
        legend_id="drummer.example",
        profile=profile,
        domain_features={
            LegendDomain.RHYTHM_SUBDIVISION: (
                DrumLegendFeature.RIDE_SURFACE_FLEXIBILITY.value,
            ),
        },
    )
    return project_legend_views(((view, 1.0),), active_tags=("fast_bebop",))


def test_shared_legend_projection_changes_bebop_ride_ranking():
    plan = DrummerSoftPlan(style_tags=frozenset({"jazz", "bop"}))
    context = DrummerRuntimeContext(position_in_bar_beats=0.0, tempo_bpm=220)
    base_projection = BebopRuntimeProjection(
        soloist=SoloistEnergyProjection(0.4, 0.5, 0.0),
        phrase_memory=BebopPhraseMemory(),
    )
    legend_projection = BebopRuntimeProjection(
        soloist=base_projection.soloist,
        phrase_memory=base_projection.phrase_memory,
        legend=ride_legend_projection(),
    )

    candidates = build_bebop_candidates(plan, context, base_projection)
    ride = next(
        g for g in candidates
        if any(hit.voice is DrumVoice.RIDE for hit in g.hits)
        and "ride_continuity" in g.tags
    )
    without = score_bebop_gesture(ride, plan, context, base_projection)
    with_legend = score_bebop_gesture(ride, plan, context, legend_projection)

    assert with_legend.score > without.score
    assert any(name == "legend_ride_surface" for name, _ in with_legend.components)


def test_runtime_projection_still_contains_no_future_legend_phrase():
    projection = BebopRuntimeProjection(
        soloist=SoloistEnergyProjection(0.4, 0.5, 0.0),
        phrase_memory=BebopPhraseMemory(),
        legend=ride_legend_projection(),
    )
    assert not hasattr(projection.legend, "future_hits")
    assert not hasattr(projection.legend, "future_phrase")
