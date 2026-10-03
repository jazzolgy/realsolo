from music_intelligence.corpus.form_sources import discover_form_sources
from music_intelligence.corpus.registry import (
    CorpusAccess,
    CorpusItem,
    CorpusKind,
    CorpusRegistry,
    CorpusUse,
)
from music_intelligence.form_intelligence import (
    FormObservation,
    PerformancePhase,
    SharedFormIntelligence,
)
from music_intelligence.learning.form_position import FormMap, FormSection


def form_map():
    return FormMap(
        form_id="AABA32",
        meter_numerator=4,
        meter_denominator=4,
        cycle_measures=32,
        sections=(
            FormSection("A1",0,8),
            FormSection("A2",8,8),
            FormSection("B",16,8),
            FormSection("A3",24,8),
        ),
    )


def test_shared_form_intelligence_refuses_to_invent_metric_position():
    engine=SharedFormIntelligence(song_id="autumn_leaves")
    state=engine.update(FormObservation(
        source_time_s=12.0,
        beat_confidence=.9,
        provenance=("audio",),
    ))
    assert state.learning_ready is False
    assert state.position.measure_index is None
    assert state.position.beat_in_measure is None


def test_expected_form_plus_absolute_beat_resolves_shared_address():
    engine=SharedFormIntelligence(song_id="autumn_leaves")
    engine.set_expected_form(form_map(),source_id="realchord:autumn_leaves")
    state=engine.update(FormObservation(
        source_time_s=18.4,
        absolute_beat=18*4+2.0,
        beat_confidence=.95,
        meter_confidence=.95,
        form_confidence=.9,
        phase_hint=PerformancePhase.SOLO,
        within_core_form=True,
        provenance=("beat_meter_intelligence",),
    ))
    assert state.learning_ready is True
    assert state.form_ready is True
    assert state.position.section_id == "B"
    assert state.position.measure_index == 18
    assert state.position.beat_in_measure == 2.0
    assert state.performance_phase is PerformancePhase.SOLO
    assert state.distance_to_boundary_measures == 5.0


def test_metric_only_resolution_works_without_form_prior():
    engine=SharedFormIntelligence(song_id="unknown")
    state=engine.update(FormObservation(
        source_time_s=4.0,
        absolute_beat=5.0,
        meter_numerator=4,
        meter_denominator=4,
        beat_confidence=.9,
        meter_confidence=.8,
    ))
    assert state.position.measure_index == 1
    assert state.position.beat_in_measure == 1.0
    assert state.form_ready is False


def test_realchord_tagged_source_is_preferred_over_generic_chart():
    registry=CorpusRegistry((
        CorpusItem(
            item_id="chart:x",
            kind=CorpusKind.MUSICAL_INTELLIGENCE,
            media_type="text/plain",
            title="Autumn Leaves",
            local_relpath="symbolic/autumn.txt",
            access=CorpusAccess.LOCAL_PRIVATE,
            uses=frozenset({CorpusUse.RESEARCH}),
            tags=frozenset({"chord_chart"}),
        ),
        CorpusItem(
            item_id="realchord:x",
            kind=CorpusKind.MUSICAL_INTELLIGENCE,
            media_type="application/json",
            title="Autumn Leaves",
            local_relpath="annotations/realchord/autumn.json",
            access=CorpusAccess.LOCAL_PRIVATE,
            uses=frozenset({CorpusUse.RESEARCH}),
            tags=frozenset({"realchord","form_map","measure_map"}),
        ),
    ))
    found=discover_form_sources(registry,title="Autumn Leaves")
    assert found[0].item_id == "realchord:x"
    assert found[0].is_realchord is True
