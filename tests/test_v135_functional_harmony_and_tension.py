import pytest

from music_intelligence.harmony.contextual_tension import (
    MusicalLayer,
    TensionContext,
    TensionUse,
    assess_tension,
)
from music_intelligence.harmony.functional_graph import (
    FunctionFamily,
    FunctionalNode,
    HarmonicFunctionGraph,
    MetricStress,
    ResolutionKind,
    dominant_expected_resolution,
    infer_dominant_family,
    make_resolution_edge,
)


def test_secondary_and_extended_dominants_depend_on_context_not_symbol_alone():
    assert infer_dominant_family(
        root_is_diatonic=True,
        metric_stress=MetricStress.WEAK,
    ) is FunctionFamily.SECONDARY_DOMINANT
    assert infer_dominant_family(
        root_is_diatonic=False,
        metric_stress=MetricStress.STRONG,
        continues_dominant_chain=True,
    ) is FunctionFamily.EXTENDED_DOMINANT


def test_substitute_dominant_uses_half_step_resolution_expectation():
    assert dominant_expected_resolution(
        FunctionFamily.SUBSTITUTE_DOMINANT
    ) is ResolutionKind.DOWN_HALF_STEP


def test_deceptive_resolution_does_not_erase_source_function():
    g7 = FunctionalNode(
        "g7", 7, "G7", FunctionFamily.SECONDARY_DOMINANT,
        key_context="C", target_degree="V",
    )
    em7 = FunctionalNode("em7", 4, "Em7", FunctionFamily.TONIC)
    graph = HarmonicFunctionGraph()
    graph.add_node(g7)
    graph.add_node(em7)
    edge = make_resolution_edge(g7, em7, actual_deceptive=True)
    graph.add_edge(edge)
    assert edge.expected_resolution is ResolutionKind.DOWN_PERFECT_FIFTH
    assert edge.actual_resolution is ResolutionKind.DECEPTIVE
    assert edge.preserves_source_function is True


def test_graph_keeps_alternative_analysis_nodes_separate():
    graph = HarmonicFunctionGraph()
    graph.add_node(FunctionalNode("d1", 1, "Db7", FunctionFamily.SUBSTITUTE_DOMINANT))
    graph.add_node(FunctionalNode("d2", 1, "Db7", FunctionFamily.SPECIAL_FUNCTION_DOMINANT))
    assert graph.nodes["d1"].family != graph.nodes["d2"].family


def test_scale_approach_can_be_melodically_valid_but_harmonically_weak():
    a = assess_tension(TensionContext(
        layer=MusicalLayer.MELODY,
        is_nonbasic_scale_tone=True,
        duration_beats=.5,
        followed_by_step_to_chord_tone=True,
    ))
    assert a.melodic_availability > a.harmonic_support_availability
    assert a.resolution_need > .45


def test_long_nonchord_melody_note_is_classified_as_melodic_tension():
    a = assess_tension(TensionContext(
        layer=MusicalLayer.MELODY,
        is_nonbasic_scale_tone=True,
        duration_beats=1.5,
    ))
    assert a.use is TensionUse.MELODIC_TENSION


def test_harmonic_tension_written_in_symbol_is_supported():
    a = assess_tension(TensionContext(
        layer=MusicalLayer.SUPPORTING_HARMONY,
        is_nonbasic_scale_tone=True,
        included_in_chord_symbol=True,
        duration_beats=2.0,
        exposed=True,
    ))
    assert a.use is TensionUse.HARMONIC_TENSION
    assert a.harmonic_support_availability > .6


def test_unspecified_altered_accompaniment_tension_is_more_cautious():
    explicit = assess_tension(TensionContext(
        layer=MusicalLayer.SUPPORTING_HARMONY,
        is_nonbasic_scale_tone=True,
        altered=True,
        included_in_chord_symbol=True,
        exposed=True,
    ))
    implicit = assess_tension(TensionContext(
        layer=MusicalLayer.SUPPORTING_HARMONY,
        is_nonbasic_scale_tone=True,
        altered=True,
        included_in_chord_symbol=False,
        exposed=True,
    ))
    assert explicit.harmonic_support_availability > implicit.harmonic_support_availability


def test_modal_characteristic_tone_is_not_hardcoded_as_avoid_note():
    a = assess_tension(TensionContext(
        layer=MusicalLayer.SUPPORTING_HARMONY,
        is_nonbasic_scale_tone=True,
        modal_context=True,
        characteristic_modal_tone=True,
        exposed=True,
    ))
    assert a.harmonic_support_availability > .35
    assert a.resolution_need < .45


def test_contextual_tension_has_no_required_scale_or_exact_future_notes():
    a = assess_tension(TensionContext(layer=MusicalLayer.MELODY))
    assert not hasattr(a, "required_scale")
    assert not hasattr(a, "exact_future_notes")
