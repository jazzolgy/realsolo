from music_intelligence.reasoning.online_improviser import OnlineMusicalEvaluator, PerformanceMemory

from realtime.ensemble_app.beat_tracker import AdaptiveBeatTracker
from realtime.ensemble_app.core_bridge import CoreImmediateBridge, DiagnosticResponseFactory
from realtime.ensemble_app.engine import EnsembleEngine
from realtime.ensemble_app.models import MidiObservation, MusicalAction, ObservationKind
from realtime.ensemble_app.scheduler import RealtimeScheduler


def note(t, pitch=60, velocity=80):
    return MidiObservation(t, ObservationKind.NOTE_ON, note=pitch, velocity=velocity)


def test_chord_attacks_cluster_instead_of_corrupting_tempo():
    tracker = AdaptiveBeatTracker()
    for base in (0.0, 0.5, 1.0, 1.5, 2.0, 2.5):
        tracker.update(note(base, 60))
        tracker.update(note(base + 0.012, 64))
        state = tracker.update(note(base + 0.025, 67))
    assert state.tempo_bpm is not None
    assert abs(state.tempo_bpm - 120.0) < 4.0


def test_phrase_end_is_emitted_once_after_space():
    bridge = CoreImmediateBridge(DiagnosticResponseFactory(), OnlineMusicalEvaluator(), PerformanceMemory())
    engine = EnsembleEngine(bridge, lambda _: None, clock=lambda: 0.0)
    engine.ingest(note(0.0, 72))
    engine.ingest(note(0.5, 74))
    first = engine.tick(1.2)
    assert first.phrase.phrase_end is True
    second = engine.tick(1.3)
    assert second.phrase.phrase_end is False


def test_new_plan_cancels_future_start_but_not_committed_note_off():
    played = []
    scheduler = RealtimeScheduler(played.append, clock=lambda: 0.0)
    scheduler.replace_plan([MusicalAction(60, 70, duration_s=1.0, delay_s=0.0)], now=0.0)
    scheduler.drain_due(0.0)
    assert played[-1].kind == "note_on"

    scheduler.replace_plan([MusicalAction(62, 70, duration_s=0.2, delay_s=0.5)], now=0.1)
    scheduler.replace_plan([], now=0.2)
    scheduler.drain_due(1.1)

    assert any(x.kind == "note_off" and x.pitch_midi == 60 for x in played)
    assert not any(x.kind == "note_on" and x.pitch_midi == 62 for x in played)


def test_diagnostic_bridge_uses_shared_core_one_event_memory():
    memory = PerformanceMemory()
    bridge = CoreImmediateBridge(DiagnosticResponseFactory(), OnlineMusicalEvaluator(), memory)
    engine = EnsembleEngine(bridge, lambda _: None, clock=lambda: 0.0)
    for i, pitch in enumerate((60, 62, 64, 65)):
        engine.ingest(note(i * 0.5, pitch))
    state = engine.tick(2.7)
    assert state.phrase.phrase_end
    assert len(memory.committed) >= 1
    assert len(bridge.decide(state, "phrase_end")) <= 1
