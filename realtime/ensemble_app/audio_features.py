from __future__ import annotations

from dataclasses import dataclass

from .models import AudioObservation


class AudioFeatureBackendUnavailable(RuntimeError):
    pass


def _np():
    try:
        import numpy as np
    except ImportError as exc:
        raise AudioFeatureBackendUnavailable(
            'Install audio support with: pip install -e ".[audio]"'
        ) from exc
    return np


@dataclass
class AudioFeatureExtractor:
    """Streaming, causal microphone features for the realtime hot path.

    This is intentionally a perception front-end, not the final MIR model.
    Better onset/pitch/timbre models can replace it while preserving the
    AudioObservation contract used by the ensemble runtime.
    """

    sample_rate: int = 48000
    min_pitch_hz: float = 65.0
    max_pitch_hz: float = 1400.0
    onset_sensitivity: float = 2.8
    min_onset_rms: float = 0.006

    def __post_init__(self) -> None:
        self._prev_mag = None
        self._flux_mean = 0.0
        self._flux_dev = 1e-6
        self._frames = 0

    def process(self, samples, timestamp: float) -> AudioObservation:
        np = _np()
        x = np.asarray(samples, dtype=np.float32).reshape(-1)
        if x.size == 0:
            return AudioObservation(timestamp, 0.0, 0.0)

        # Remove DC; microphone gain is intentionally not normalized away.
        x = x - float(np.mean(x))
        rms = float(np.sqrt(np.mean(x * x) + 1e-12))
        peak = float(np.max(np.abs(x)))

        window = np.hanning(x.size).astype(np.float32)
        mag = np.abs(np.fft.rfft(x * window))
        if self._prev_mag is None or self._prev_mag.shape != mag.shape:
            flux = 0.0
        else:
            diff = mag - self._prev_mag
            flux = float(np.sum(diff[diff > 0]) / (np.sum(self._prev_mag) + 1e-9))
        self._prev_mag = mag

        self._frames += 1
        alpha = 0.06 if self._frames > 8 else 0.25
        delta = flux - self._flux_mean
        self._flux_mean += alpha * delta
        self._flux_dev = (1 - alpha) * self._flux_dev + alpha * abs(delta)
        threshold = self._flux_mean + self.onset_sensitivity * max(self._flux_dev, 1e-5)
        onset = self._frames > 4 and rms >= self.min_onset_rms and flux > threshold

        pitch_hz, pitch_conf = self._estimate_pitch(x, rms)
        return AudioObservation(
            timestamp=timestamp,
            rms=rms,
            peak=peak,
            onset_strength=flux,
            onset=bool(onset),
            pitch_hz=pitch_hz,
            pitch_confidence=pitch_conf,
        )

    def _estimate_pitch(self, x, rms: float) -> tuple[float | None, float]:
        if rms < self.min_onset_rms * 0.6:
            return None, 0.0
        np = _np()
        if x.size < 128:
            return None, 0.0

        # Baseline monophonic evidence: dominant spectral peak with quadratic
        # interpolation. This avoids the strong subharmonic ambiguity of raw
        # autocorrelation while remaining causal and cheap enough for the
        # development harness. Polyphonic/learned pitch models can replace it.
        window = np.hanning(x.size).astype(np.float32)
        spectrum = np.abs(np.fft.rfft(x * window))
        freqs = np.fft.rfftfreq(x.size, 1.0 / self.sample_rate)
        mask = (freqs >= self.min_pitch_hz) & (freqs <= self.max_pitch_hz)
        indexes = np.flatnonzero(mask)
        if indexes.size < 3:
            return None, 0.0

        local = spectrum[indexes]
        rel = int(np.argmax(local))
        k = int(indexes[rel])
        peak = float(spectrum[k])
        if peak <= 1e-9:
            return None, 0.0

        # Quadratic interpolation around the FFT bin.
        delta = 0.0
        if 0 < k < len(spectrum) - 1:
            a = float(spectrum[k - 1])
            b = float(spectrum[k])
            g = float(spectrum[k + 1])
            denom = a - 2.0 * b + g
            if abs(denom) > 1e-12:
                delta = 0.5 * (a - g) / denom
                delta = max(-0.5, min(0.5, delta))

        pitch_hz = (k + delta) * self.sample_rate / x.size
        floor = float(np.median(local)) + 1e-9
        confidence = peak / (peak + 8.0 * floor)
        if confidence < 0.35:
            return None, confidence
        return float(pitch_hz), min(1.0, max(0.0, confidence))
