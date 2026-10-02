from music_intelligence.corpus import (
    ALONG_CAME_BETTY_EVIDENCE,
    ALONG_CAME_BETTY_LOCATOR,
    ScorePerformancePhase,
    ScorePosition,
    resolve_score_context,
)


def _snap(page, bar, phase):
    return resolve_score_context(
        ALONG_CAME_BETTY_LOCATOR,
        ScorePosition(page=page, bar=bar),
        ALONG_CAME_BETTY_EVIDENCE,
        phase=phase,
    )


def test_index_locator_identity_and_pages():
    loc = ALONG_CAME_BETTY_LOCATOR
    assert loc.book_id == "scorebook.newreal.2"
    assert loc.start_page == 7
    assert loc.end_page == 8


def test_head_and_solo_can_share_same_bar_without_activity_confusion():
    head = _snap(7, 1, ScorePerformancePhase.HEAD)
    solo = _snap(7, 1, ScorePerformancePhase.SOLO)
    assert head.section == "A"
    assert head.written_melody_active
    assert head.solo_indication is None
    assert solo.section == "A"
    assert not solo.written_melody_active
    assert solo.solo_indication == "open solo on form ABC"


def test_unknown_phase_does_not_guess_head_or_solo():
    snap = _snap(7, 1, ScorePerformancePhase.UNKNOWN)
    assert not snap.written_melody_active
    assert snap.solo_indication is None
    assert any(x.phases for x in snap.unresolved_evidence)


def test_core_chart_identity_style_tempo_meter_and_harmony():
    snap = _snap(7, 10, ScorePerformancePhase.SOLO)
    assert "medium swing" in snap.style
    assert snap.tempo == "quarter=110"
    assert snap.meter == "4/4"
    assert snap.section == "A"
    assert snap.chords == ("Gm7 C7",)
    assert "solo on form ABC" in snap.form


def test_regular_and_last_solo_endings_are_distinguished():
    regular = _snap(7, 33, ScorePerformancePhase.SOLO)
    last = _snap(7, 33, ScorePerformancePhase.SOLO_LAST)
    assert "Use Till Cue ending" in regular.navigation
    assert "Take On Cue ending to last solo" not in regular.navigation
    assert "Take On Cue ending to last solo" in last.navigation


def test_d_is_written_ensemble_section_not_solo_form():
    d = _snap(8, 35, ScorePerformancePhase.HEAD)
    assert d.section == "D"
    assert d.written_part_role == "D: written trumpet and tenor ensemble parts"
    assert d.solo_indication is None
    assert d.chords == ("Bbm7",)


def test_ds_al_coda_and_coda_harmony_are_preserved():
    ds = _snap(8, 50, ScorePerformancePhase.HEAD)
    coda = _snap(8, 51, ScorePerformancePhase.HEAD)
    assert "D.S. al Coda" in ds.navigation
    assert coda.section == "Coda"
    assert coda.chords == ("Eb7#9",)
    assert "Coda" in coda.navigation


def test_arrangement_instructions_remain_evidence_not_sax_policy():
    solo = _snap(8, 44, ScorePerformancePhase.SOLO)
    assert "No kicks during solos." in solo.arrangement_notes
    assert "Piano lays out at A during solos." in solo.arrangement_notes
