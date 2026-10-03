from music_intelligence.legends.interfaces import (
    LegendDomain,
    VocabularyQuery,
    VocabularyUseType,
)
from music_intelligence.vocabulary import (
    SHARED_VOCABULARY_INDEX,
    SHARED_VOCABULARY_ITEMS,
)
from music_intelligence.reasoning.runtime_vocabulary import project_shared_vocabulary
from realtime.ensemble_app.stage1_quartet import Stage1QuartetRuntime


def _tick(runtime):
    return runtime.decide(
        "Cm7","F7",
        beat_in_bar=0.0,
        bar_index=0,
        total_bars=32,
        tempo_bpm=172.0,
        section="A",
    )


def test_shared_catalog_is_broad_and_non_literal():
    assert len(SHARED_VOCABULARY_ITEMS) >= 45
    assert all(not x.literal_representation for x in SHARED_VOCABULARY_ITEMS)
    assert all(
        VocabularyUseType.LITERAL_QUOTE not in x.candidate_uses
        for x in SHARED_VOCABULARY_ITEMS
    )
    ids={x.vocabulary_id for x in SHARED_VOCABULARY_ITEMS}
    assert len(ids)==len(SHARED_VOCABULARY_ITEMS)


def test_shared_catalog_contains_solo_piano_bass_drums_and_ensemble_knowledge():
    ids={x.vocabulary_id for x in SHARED_VOCABULARY_ITEMS}
    required={
        "shared.solo.target_next_harmony",
        "shared.bebop.close_approach",
        "shared.piano.lay_out",
        "shared.bass.last_beat_approach",
        "shared.drums.ride_quarter_field",
        "shared.ensemble.form_knowledge_not_marking",
        "shared.ensemble.meter_not_pulse_responsibility",
    }
    assert required.issubset(ids)


def test_shared_vocabulary_is_queryable_without_named_legend():
    rows=SHARED_VOCABULARY_INDEX.query(VocabularyQuery(
        legend_id="shared",
        domain=LegendDomain.LINEAR_CONNECTION,
        target_instrument="tenor_sax",
        limit=12,
    ))
    assert rows
    assert any("bebop" in x.context_tags for x in rows)


def test_player_neutral_projection_returns_instrument_relevant_items():
    bass=project_shared_vocabulary(
        SHARED_VOCABULARY_INDEX,
        player_id="bass",
        target_instrument="bass",
        domains=(LegendDomain.LINEAR_CONNECTION,LegendDomain.FORM_AWARENESS),
    )
    drums=project_shared_vocabulary(
        SHARED_VOCABULARY_INDEX,
        player_id="drums",
        target_instrument="drums",
        domains=(LegendDomain.RHYTHM_SUBDIVISION,LegendDomain.ENSEMBLE_INTERACTION),
    )
    assert any(x.vocabulary_id.startswith("shared.bass.") for x in bass.items)
    assert any(x.vocabulary_id.startswith("shared.drums.") for x in drums.items)


def test_autumn_leaves_sax_consumes_shared_vocabulary_as_motif_seed():
    quartet=Stage1QuartetRuntime.create(172.0)
    quartet.legend_showcase=True
    result=_tick(quartet)
    sax=next(
        g for g in result.gestures
        if g.source=="player/sax:canonical_immediate"
    )
    assert int(sax.annotations["shared_vocabulary_count"]) > 0
    assert sax.annotations["shared_vocabulary_seed"].startswith("shared.")
    sax_decision=next(d for d in result.decisions if d.player_id=="sax")
    assert "shared_vocabulary_runtime" in sax_decision.intent.provenance
