from pathlib import Path
import zipfile

from music_intelligence.corpus import (
    ALL_PLAYER_INSTRUMENTS,
    CorpusRegistry,
    STANDARD_100_TITLES,
    chart_item_id,
    install_standard_100_from_archive,
    register_standard_100,
    standard_100_corpus_items,
)


def test_standard100_manifest_has_exactly_100_unique_titles():
    assert len(STANDARD_100_TITLES) == 100
    assert len(set(STANDARD_100_TITLES)) == 100


def test_standard100_is_shared_across_all_player_domains():
    items = standard_100_corpus_items()
    assert len(items) == 101  # parent dataset + 100 charts
    for item in items[1:]:
        assert item.instruments == ALL_PLAYER_INSTRUMENTS
        assert "shared_core" in item.tags


def test_registry_uses_stable_chart_ids():
    registry = CorpusRegistry()
    register_standard_100(registry)
    autumn = registry.get(chart_item_id("Autumn Leaves"))
    assert autumn.title == "Autumn Leaves"
    assert autumn.local_relpath.endswith("autumn_leaves.krn")


def test_installer_preserves_raw_chart_text_and_reports_missing(tmp_path: Path):
    archive = tmp_path / "irealb.zip"
    autumn = (
        "!!!OTL: Autumn Leaves\n"
        "!!!COM: Joseph Kosma\n"
        "**harm\n"
        "*M4/4\n"
        "Cm7\n"
        "F7\n"
        "*-\n"
    )
    doxy = (
        "!!!OTL: Doxy\n"
        "**harm\n"
        "*M4/4\n"
        "Bb7\n"
        "*-\n"
    )
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("nested/autumn.krn", autumn)
        zf.writestr("nested/doxy.krn", doxy)

    report = install_standard_100_from_archive(archive, root=tmp_path / "corpus")
    assert "Autumn Leaves" in report.installed_titles
    assert "Doxy" in report.installed_titles
    assert "Cherokee" in report.missing_titles
    installed = report.destination / "autumn_leaves.krn"
    assert installed.read_text() == autumn
