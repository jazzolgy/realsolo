from realtime.ensemble_app.learned_instrument_adapter import (
    HybridInstrumentRoleDetector,
    LearnedInstrumentRoleAdapter,
)
from realtime.ensemble_app.instrument_role_detector import AcousticDescriptorFrame
from realtime.ensemble_app.musical_context_corrector import (
    MusicalContextCorrector,
    MusicalContextFrame,
)
from realtime.ensemble_app.models import BeatState, PhraseState
from music_intelligence.learning.shared_audio_intelligence import (
    ContextCorrection,
    DetectorEvidence,
    PerformanceEvidence,
    musical_moment_from_evidence,
)


class FakeBackend:
    def predict(self, samples, *, sample_rate: int):
        return (
            {"Trumpet": .72, "flugelhorn": .18, "mystery horn": .05},
            {"solo": .76, "ensemble": .12},
            {"model": .83},
        )


def frame():
    return AcousticDescriptorFrame(
        pitch_hz=440.0,
        pitch_confidence=.9,
        onset=True,
        onset_strength=.4,
        rms=.12,
        spectral_centroid_hz=1800,
        spectral_flatness=.1,
        zero_crossing_rate=.04,
        low_energy_ratio=.12,
        mid_energy_ratio=.78,
        high_energy_ratio=.10,
    )


def test_learned_adapter_normalizes_known_and_open_labels():
    detector=HybridInstrumentRoleDetector(
        learned=LearnedInstrumentRoleAdapter(FakeBackend())
    )
    raw=detector.detect([0.0],sample_rate=48000,frame=frame())
    assert "trumpet" in raw.instrument_probabilities
    assert "open:mystery_horn" in raw.instrument_probabilities
    assert raw.role_probabilities["solo"] > raw.role_probabilities["ensemble"]


def test_musical_context_reweights_only_existing_labels():
    raw=DetectorEvidence(
        instrument_probabilities={"trumpet":.65,"saxophone":.2},
        role_probabilities={"melody_or_solo":.55,"comping_or_support":.2},
        confidence_fields={"event":.8},
        pitch_hz=440.0,
        onset=True,
        onset_strength=.4,
        rms=.1,
    )
    prior=ContextCorrection(
        instrument_probabilities=dict(raw.instrument_probabilities),
        role_probabilities=dict(raw.role_probabilities),
        confidence_fields={"event":.8},
        reasons=("temporal_instrument_continuity",),
    )
    ctx=MusicalContextFrame(
        beat=BeatState(tempo_bpm=120,beat_period_s=.5,phase=.05,confidence=.8,anchor_time=0),
        phrase=PhraseState(active=True,attack_count=4,last_attack_time=1.0),
        pitch_hz=440.0,
        onset=True,
    )
    post=MusicalContextCorrector().correct(raw,prior,ctx)
    assert set(post.instrument_probabilities)=={"trumpet","saxophone"}
    assert "flute" not in post.instrument_probabilities
    assert post.role_probabilities["melody_or_solo"] > prior.role_probabilities["melody_or_solo"]


def test_musical_moment_accepts_measured_tempo_beat_and_register():
    raw=DetectorEvidence(
        instrument_probabilities={"trumpet":.7},
        role_probabilities={"solo":.7},
        confidence_fields={"event":.8},
        pitch_hz=440.0,
        onset=True,
    )
    post=ContextCorrection(
        instrument_probabilities={"trumpet":.72},
        role_probabilities={"solo":.73},
        confidence_fields={"event":.82},
    )
    ev=PerformanceEvidence("youtube:x",2.0,raw,post)
    moment=musical_moment_from_evidence(
        ev,tempo_bpm=120.0,beat_position=.25,register_center=69.0
    )
    assert moment.tempo_bpm==120.0
    assert moment.beat_position==.25
    assert moment.register_center==69.0
    assert moment.tension is None
