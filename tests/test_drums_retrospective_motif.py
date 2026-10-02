from music_intelligence.drums.comping_phrase import (
    CommittedSnareEvent,
    SnarePhraseMemory,
    motif_from_recent_events,
    record_committed_snare_event,
)


def test_two_committed_hits_create_retrospective_motif():
    motif = motif_from_recent_events((
        CommittedSnareEvent(3, 0.25, 0.5),
        CommittedSnareEvent(3, 0.625, 0.8),
    ))
    assert motif is not None
    assert motif.onset_phases == (0.25, 0.625)
    assert motif.accent_phases == (0.625,)
    assert motif.source == "retrospective_local_execution"


def test_retrospective_motif_caps_at_four_recent_hits():
    motif = motif_from_recent_events(tuple(
        CommittedSnareEvent(4, phase)
        for phase in (0.0, 0.125, 0.25, 0.5, 0.75)
    ))
    assert motif is not None
    assert len(motif.onset_phases) == 4
    assert motif.onset_phases == (0.125, 0.25, 0.5, 0.75)


def test_events_outside_one_bar_span_do_not_form_false_cell():
    motif = motif_from_recent_events((
        CommittedSnareEvent(1, 0.1),
        CommittedSnareEvent(3, 0.1),
    ))
    assert motif is None


def test_recording_only_played_events_updates_motif_without_future_notes():
    memory = SnarePhraseMemory()
    memory = record_committed_snare_event(memory, bar_index=2, phase=0.25, accent=0.5)
    assert memory.motif is None
    memory = record_committed_snare_event(memory, bar_index=2, phase=0.625, accent=0.8)
    assert memory.motif is not None
    assert memory.motif.onset_phases == (0.25, 0.625)
    assert not hasattr(memory, "future_events")
