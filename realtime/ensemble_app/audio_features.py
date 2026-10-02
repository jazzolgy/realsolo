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
        # Downsample cheaply for a bounded autocorrelation search.
        decim = max(1, self.sample_rate // 12000)
        y = x[::decim]
        sr = self.sample_rate / decim
        if y.size < 64:
            return None, 0.0

        min_lag = max(2, int(sr / self.max_pitch_hz))
        max_lag = min(y.size // 2, int(sr / self.min_pitch_hz))
        if max_lag <= min_lag:
            return None, 0.0

        y = y - float(np.mean(y))
        energy = float(np.dot(y, y)) + 1e-9
        best_lag = None
        best = -1.0
        for lag in range(min_lag, max_lag + 1):
            a = y[:-lag]
            b = y[lag:]
            denom = float(np.sqrt(np.dot(a, a) * np.dot(b, b))) + 1e-9
            score = float(np.dot(a, b) / denom)
            if score > best:
                best = score
                best_lag = lag

        if best_lag is None or best < 0.35:
            return None, max(0.0, best)
        return float(sr / best_lag), min(1.0, max(0.0, best))
