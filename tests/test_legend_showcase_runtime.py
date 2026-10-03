from realtime.ensemble_app.stage1_quartet import Stage1QuartetRuntime
from music_intelligence.reasoning.runtime_legend_selector import (
    legend_choice_for,
    select_showcase_legends,
)


def _tick(runtime, beat=0.0):
    return runtime.decide(
        "Cm7","F7",
        beat_in_bar=beat,
        bar_index=0,
        total_bars=32,
        tempo_bpm=172.0,
        section="A",
    )


def test_showcase_activates_all_currently_usable_promoted_legends():
    choices=select_showcase_legends(style_tags=("jazz","bebop","swing"))
    assert legend_choice_for(choices,"sax").legend_id=="charlie_parker"
    assert legend_choice_for(choices,"sax").weight==1.0
    assert legend_choice_for(choices,"bass").legend_id=="scott_lafaro"
    assert legend_choice_for(choices,"bass").weight==1.0
    # Bill Evans is intentionally absent until actual tendencies are promoted.
    assert legend_choice_for(choices,"piano") is None


def test_showcase_sax_exposes_full_parker_material_pool():
    quartet=Stage1QuartetRuntime.create(172.0)
    quartet.legend_showcase=True
    result=_tick(quartet)
    sax=next(
        g for g in result.gestures
        if g.source=="player/sax:canonical_immediate"
    )
    assert sax.annotations["legend_id"]=="charlie_parker"
    assert sax.annotations["legend_showcase"]=="1"
    assert int(sax.annotations["legend_material_count"]) >= 6


def test_showcase_passes_lafaro_id_through_existing_bass_context_contract():
    quartet=Stage1QuartetRuntime.create(172.0)
    quartet.legend_showcase=True
    result=_tick(quartet)
    bass=next(
        g for g in result.gestures
        if g.source=="player/bass:sequential_runner"
    )
    assert bass.annotations["legend_id"]=="scott_lafaro"


def test_non_showcase_keeps_conservative_selection():
    quartet=Stage1QuartetRuntime.create(172.0)
    result=_tick(quartet)
    sax=next(
        g for g in result.gestures
        if g.source=="player/sax:canonical_immediate"
    )
    assert sax.annotations["legend_showcase"]=="0"
