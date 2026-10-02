import math

import numpy as np

from music_intelligence.reasoning.online_improviser import OnlineMusicalEvaluator, PerformanceMemory
from realtime.ensemble_app.audio_features import AudioFeatureExtractor
from realtime.ensemble_app.core_bridge import CoreImmediateBridge, DiagnosticResponseFactory
from realtime.ensemble_app.engine import EnsembleEngine


def sine(freq, sr=48000, n=4096, amp=0.2):
    t = np.arange(n, dtype=np.float32) / sr
    return (amp * np.sin(2 * math.pi * freq * t)).astype(np.float32)


def test_audio_pitch_evidence_finds_a4_near_440():
    ext = AudioFeatureExtractor(sample_rate=48000)
    obs = ext.process(sine(440.0), 0.0)
    assert obs.pitch_hz is not None
    assert abs(obs.pitch_hz - 440.0) < 12.0
    assert obs.pitch_confidence > 0.5


def test_audio_observation_updates_shared_ensemble_state():
    ext = AudioFeatureExtractor(sample_rate=48000)
    bridge = CoreImmediateBridge(DiagnosticResponseFactory(), OnlineMusicalEvaluator(), PerformanceMemory())
    engine = EnsembleEngine(bridge, lambda _: None, clock=lambda: 0.0)
    obs = ext.process(sine(330.0), 1.0)
    state = engine.ingest(obs)
    assert state.input_mode == "audio"
    assert state.audio_rms > 0
    assert state.audio_pitch_hz is not None


def test_audio_and_midi_can_share_one_ensemble_state():
    from realtime.ensemble_app.models import MidiObservation, ObservationKind

    ext = AudioFeatureExtractor(sample_rate=48000)
    bridge = CoreImmediateBridge(DiagnosticResponseFactory(), OnlineMusicalEvaluator(), PerformanceMemory())
    engine = EnsembleEngine(bridge, lambda _: None, clock=lambda: 0.0)
    engine.ingest(ext.process(sine(220.0), 1.0))
    state = engine.ingest(MidiObservation(1.1, ObservationKind.NOTE_ON, note=60, velocity=90))
    assert state.input_mode == "hybrid"
    assert 60 in state.active_notes


def test_clock_tick_does_not_turn_audio_session_into_hybrid():
    ext = AudioFeatureExtractor(sample_rate=48000)
    bridge = CoreImmediateBridge(DiagnosticResponseFactory(), OnlineMusicalEvaluator(), PerformanceMemory())
    engine = EnsembleEngine(bridge, lambda _: None, clock=lambda: 0.0)
    engine.ingest(ext.process(sine(220.0), 1.0))
    state = engine.tick(1.1)
    assert state.input_mode == "audio"
