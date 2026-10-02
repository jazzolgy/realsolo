import json

from music_intelligence.drums.standard100_practice import (
    discover_standard100_files,
    load_standard100,
    practice_standard100,
)


def write_chart(path, title, bars=8, tempo=160, meter="4/4"):
    path.write_text(json.dumps({
        "title": title,
        "tempo": tempo,
        "meter": meter,
        "bar_count": bars,
        "sections": [{"label": "A", "bars": bars}],
    }), encoding="utf-8")


def test_standard100_runner_reads_private_layout_and_practices_all_source_bars(tmp_path):
    root = tmp_path / "corpus"
    charts = root / "symbolic" / "irealb_v1_0" / "standard100"
    charts.mkdir(parents=True)
    write_chart(charts / "one.json", "One", bars=8)
    write_chart(charts / "two.json", "Two", bars=12)

    assert len(discover_standard100_files(root)) == 2
    loaded = load_standard100(root)
    assert {x.title for x in loaded} == {"One", "Two"}

    report = practice_standard100(root, passes=2, write_report=True)
    assert report.songs_practiced == 2
    assert report.total_bars_practiced == 40
    assert report.total_decisions > 0
    assert (root / "derived" / "drums" / "standard100" / "practice_report.json").exists()


def test_missing_chart_fields_are_not_silently_invented_as_source_facts(tmp_path):
    root = tmp_path / "corpus"
    charts = root / "symbolic" / "irealb_v1_0" / "standard100"
    charts.mkdir(parents=True)
    (charts / "opaque.txt").write_text("some private chart representation", encoding="utf-8")

    report = practice_standard100(root, passes=1, write_report=False)
    result = report.results[0]
    assert result.practiced is False
    assert "not_practiced_without_source_bar_count" in result.exercise_notes


def test_runner_uses_walking_bass_and_exercises_multiple_interaction_states(tmp_path):
    root = tmp_path / "corpus"
    charts = root / "symbolic" / "irealb_v1_0" / "standard100"
    charts.mkdir(parents=True)
    write_chart(charts / "one.json", "One", bars=16, tempo=180)

    report = practice_standard100(root, passes=4, write_report=False)
    result = report.results[0]
    assert result.build_states > 0
    assert result.coast_states > 0
    assert result.come_down_states > 0
    assert result.handoff_states > 0
    assert result.ride_quarter_actions > 0
