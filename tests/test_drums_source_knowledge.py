from music_intelligence.drums.knowledge import rules_for
from music_intelligence.drums.source_catalog import (
    DRUM_SOURCES,
    SourcePriority,
    sources_for_contribution,
    sources_for_domain,
)


def test_core_source_library_has_cross_style_coverage():
    assert sources_for_domain("jazz")
    assert sources_for_domain("afro_cuban")
    assert sources_for_domain("rock")
    assert sources_for_domain("fusion")


def test_catalog_keeps_patterns_and_decision_sources_distinct():
    core = [s for s in DRUM_SOURCES if s.priority is SourcePriority.CORE]
    assert any("internal_hearing" in s.contribution for s in core)
    assert any("mambo" in s.contribution for s in core)
    assert any("metric_modulation" in s.contribution for s in core)


def test_source_derived_rules_cover_listening_and_physical_reality():
    listening = rules_for("listening")
    feasibility = rules_for("physical_feasibility")
    assert any(r.source_id == "moses_drum_wisdom" for r in listening)
    assert any(r.source_id == "badness_drum_programming" for r in feasibility)


def test_fill_knowledge_has_ensemble_target_and_space():
    fill_rules = rules_for("fill")
    ids = {r.rule_id for r in fill_rules}
    assert "spagnardi_fill_function" in ids
    assert "holland_space_is_material" in ids
