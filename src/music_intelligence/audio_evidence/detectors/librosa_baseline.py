"""Optional librosa baseline detectors for offline Audio Evidence validation.

These adapters are deliberately optional: librosa/numpy are imported lazily so
RealSolo's core runtime dependency set does not change. They provide a
reproducible acoustic baseline, not a production instrument-recognition model.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
from typing import Any, Sequence

from ..adapters.source import AudioSource
from .contracts import (
    OnsetDetection,
    PitchDetection,
    TimbreDetection,
    UnpitchedDetection,
)


def _optional_modules():
    try:
        import librosa
        import numpy as np
    except ImportError as exc:
        raise RuntimeError(
            "Librosa baseline adapters require optional packages 'librosa' and 'numpy'."
        ) from exc
    return librosa, np


@dataclass(frozen=True)
class DecodedAudio:
    samples: Any
    sample_rate: int
    source_offset_seconds: float


class LibrosaSourceLoader:
    """Decode a local AudioSource once and share it between baseline detectors."""

    def __init__(self, sample_rate: int = 22050, mono: bool = True):
        if sample_rate <= 0:
            raise ValueError("sample_rate must be positive")
        self.sample_rate = int(sample_rate)
        self.mono = bool(mono)
        self._cache: dict[tuple[str, str | None, float | None, float | None], DecodedAudio] = {}

    def load(self, source: AudioSource) -> DecodedAudio:
        source.validate()
        if not source.uri:
            raise ValueError("librosa baseline requires AudioSource.uri")
        path = Path(source.uri)
        if not path.exists():
            raise FileNotFoundError(path)

        key = (
            source.source_id,
            source.uri,
            source.start_seconds,
            source.end_seconds,
        )
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        librosa, _ = _optional_modules()
        offset = float(source.start_seconds or 0.0)
        duration = None
        if source.end_seconds is not None:
            duration = source.end_seconds - offset
        samples, sample_rate = librosa.load(
            str(path),
            sr=self.sample_rate,
            mono=self.mono,
            offset=offset,
            duration=duration,
        )
        decoded = DecodedAudio(
            samples=samples,
            sample_rate=int(sample_rate),
            source_offset_seconds=offset,
        )
        self._cache[key] = decoded
        return decoded


class LibrosaOnsetDetector:
    detector_id = "librosa:onset-detect:v0.1"

    def __init__(
        self,
        loader: LibrosaSourceLoader | None = None,
        *,
        hop_length: int = 512,
        delta: float = 0.07,
    ):
        self.loader = loader or LibrosaSourceLoader()
        self.hop_length = int(hop_length)
        self.delta = float(delta)

    def detect_onsets(self, source: AudioSource) -> Sequence[OnsetDetection]:
        librosa, np = _optional_modules()
        decoded = self.loader.load(source)
        envelope = librosa.onset.onset_strength(
            y=decoded.samples,
            sr=decoded.sample_rate,
            hop_length=self.hop_length,
        )
        frames = librosa.onset.onset_detect(
            onset_envelope=envelope,
            sr=decoded.sample_rate,
            hop_length=self.hop_length,
            units="frames",
            delta=self.delta,
            backtrack=False,
        )
        peak = float(np.max(envelope)) if len(envelope) else 0.0
        results: list[OnsetDetection] = []
        for index, frame in enumerate(frames):
            local_strength = float(envelope[int(frame)]) if int(frame) < len(envelope) else 0.0
            confidence = 0.0 if peak <= 0.0 else min(1.0, local_strength / peak)
            relative = float(
                librosa.frames_to_time(
                    int(frame),
                    sr=decoded.sample_rate,
                    hop_length=self.hop_length,
                )
            )
            results.append(
                OnsetDetection(
                    onset_id=f"onset:{index:06d}",
                    onset_seconds=decoded.source_offset_seconds + relative,
                    confidence=confidence,
                )
            )
        return tuple(results)


class LibrosaSpectralPeakPitchDetector:
    """Polyphonic pitch hypotheses from local STFT spectral peaks.

    This is intentionally a hypothesis generator. It must not be treated as a
    confirmed note transcription model.
    """

    detector_id = "librosa:spectral-peak-pitch:v0.1"

    def __init__(
        self,
        loader: LibrosaSourceLoader | None = None,
        *,
        n_fft: int = 4096,
        hop_length: int = 512,
        max_pitches_per_onset: int = 6,
        relative_peak_threshold: float = 0.18,
        min_frequency_hz: float = 35.0,
        max_frequency_hz: float = 4200.0,
    ):
        self.loader = loader or LibrosaSourceLoader()
        self.n_fft = int(n_fft)
        self.hop_length = int(hop_length)
        self.max_pitches_per_onset = int(max_pitches_per_onset)
        self.relative_peak_threshold = float(relative_peak_threshold)
        self.min_frequency_hz = float(min_frequency_hz)
        self.max_frequency_hz = float(max_frequency_hz)

    def detect_pitches(
        self,
        source: AudioSource,
        onsets: Sequence[OnsetDetection],
    ) -> Sequence[PitchDetection]:
        librosa, np = _optional_modules()
        decoded = self.loader.load(source)
        magnitude = np.abs(
            librosa.stft(
                decoded.samples,
                n_fft=self.n_fft,
                hop_length=self.hop_length,
            )
        )
        frequencies = librosa.fft_frequencies(
            sr=decoded.sample_rate,
            n_fft=self.n_fft,
        )
        valid = (
            (frequencies >= self.min_frequency_hz)
            & (frequencies <= self.max_frequency_hz)
        )
        valid_indices = np.flatnonzero(valid)
        results: list[PitchDetection] = []

        for onset in onsets:
            onset.validate()
            relative = onset.onset_seconds - decoded.source_offset_seconds
            frame = int(
                librosa.time_to_frames(
                    max(relative, 0.0),
                    sr=decoded.sample_rate,
                    hop_length=self.hop_length,
                )
            )
            frame = max(0, min(frame, magnitude.shape[1] - 1))
            spectrum = magnitude[:, frame]
            local = spectrum[valid_indices]
            if local.size < 3:
                continue
            local_max = float(np.max(local))
            if local_max <= 0.0:
                continue

            center = local[1:-1]
            peaks = np.flatnonzero(
                (center > local[:-2])
                & (center >= local[2:])
                & (center >= local_max * self.relative_peak_threshold)
            ) + 1
            if peaks.size == 0:
                continue
            ranked = peaks[np.argsort(local[peaks])[::-1]][: self.max_pitches_per_onset]

            for rank, local_index in enumerate(ranked, start=1):
                bin_index = int(valid_indices[int(local_index)])
                frequency = float(frequencies[bin_index])
                confidence = min(1.0, float(spectrum[bin_index]) / local_max)
                midi = float(librosa.hz_to_midi(frequency))
                results.append(
                    PitchDetection(
                        onset_id=onset.onset_id,
                        pitch_id=f"{onset.onset_id}:pitch:{rank}",
                        confidence=confidence,
                        nominal_midi=midi,
                        frequency_hz=frequency,
                    )
                )
        return tuple(results)


class LibrosaTimbreDetector:
    detector_id = "librosa:timbre:v0.1"

    def __init__(
        self,
        loader: LibrosaSourceLoader | None = None,
        *,
        hop_length: int = 512,
    ):
        self.loader = loader or LibrosaSourceLoader()
        self.hop_length = int(hop_length)

    def detect_timbre(
        self,
        source: AudioSource,
        onsets: Sequence[OnsetDetection],
    ) -> Sequence[TimbreDetection]:
        librosa, _ = _optional_modules()
        decoded = self.loader.load(source)
        centroid = librosa.feature.spectral_centroid(
            y=decoded.samples,
            sr=decoded.sample_rate,
            hop_length=self.hop_length,
        )[0]
        flatness = librosa.feature.spectral_flatness(
            y=decoded.samples,
            hop_length=self.hop_length,
        )[0]
        rolloff = librosa.feature.spectral_rolloff(
            y=decoded.samples,
            sr=decoded.sample_rate,
            hop_length=self.hop_length,
            roll_percent=0.85,
        )[0]
        rms = librosa.feature.rms(
            y=decoded.samples,
            hop_length=self.hop_length,
        )[0]
        zero_crossing = librosa.feature.zero_crossing_rate(
            decoded.samples,
            hop_length=self.hop_length,
        )[0]

        results: list[TimbreDetection] = []
        for onset in onsets:
            relative = onset.onset_seconds - decoded.source_offset_seconds
            frame = int(
                librosa.time_to_frames(
                    max(relative, 0.0),
                    sr=decoded.sample_rate,
                    hop_length=self.hop_length,
                )
            )
            frame = max(0, min(frame, len(centroid) - 1))
            results.append(
                TimbreDetection(
                    onset_id=onset.onset_id,
                    spectral_centroid_hz=float(centroid[frame]),
                    features={
                        "spectral_flatness": float(flatness[frame]),
                        "spectral_rolloff_hz": float(rolloff[frame]),
                        "rms": float(rms[frame]),
                        "zero_crossing_rate": float(zero_crossing[frame]),
                    },
                    detector_id=self.detector_id,
                )
            )
        return tuple(results)


class LibrosaPercussiveTokenDetector:
    """Weak kick/snare/cymbal hypotheses from HPSS percussive spectra."""

    detector_id = "librosa:percussive-token:v0.1"

    def __init__(
        self,
        loader: LibrosaSourceLoader | None = None,
        *,
        n_fft: int = 2048,
        hop_length: int = 512,
        minimum_percussive_ratio: float = 0.18,
    ):
        self.loader = loader or LibrosaSourceLoader()
        self.n_fft = int(n_fft)
        self.hop_length = int(hop_length)
        self.minimum_percussive_ratio = float(minimum_percussive_ratio)

    def detect_unpitched(
        self,
        source: AudioSource,
        onsets: Sequence[OnsetDetection],
    ) -> Sequence[UnpitchedDetection]:
        librosa, np = _optional_modules()
        decoded = self.loader.load(source)
        harmonic, percussive = librosa.effects.hpss(decoded.samples)
        magnitude = np.abs(
            librosa.stft(
                percussive,
                n_fft=self.n_fft,
                hop_length=self.hop_length,
            )
        )
        full = np.abs(
            librosa.stft(
                decoded.samples,
                n_fft=self.n_fft,
                hop_length=self.hop_length,
            )
        )
        frequencies = librosa.fft_frequencies(
            sr=decoded.sample_rate,
            n_fft=self.n_fft,
        )
        low = frequencies < 180.0
        mid = (frequencies >= 180.0) & (frequencies < 2500.0)
        high = frequencies >= 2500.0

        results: list[UnpitchedDetection] = []
        for onset in onsets:
            relative = onset.onset_seconds - decoded.source_offset_seconds
            frame = int(
                librosa.time_to_frames(
                    max(relative, 0.0),
                    sr=decoded.sample_rate,
                    hop_length=self.hop_length,
                )
            )
            frame = max(0, min(frame, magnitude.shape[1] - 1))
            p_energy = float(np.sum(magnitude[:, frame]))
            all_energy = float(np.sum(full[:, frame]))
            if all_energy <= 0.0:
                continue
            percussive_ratio = p_energy / all_energy
            if percussive_ratio < self.minimum_percussive_ratio:
                continue

            low_energy = float(np.sum(magnitude[low, frame]))
            mid_energy = float(np.sum(magnitude[mid, frame]))
            high_energy = float(np.sum(magnitude[high, frame]))
            total = low_energy + mid_energy + high_energy
            if total <= 0.0:
                continue
            shares = {
                "kick": low_energy / total,
                "snare": mid_energy / total,
                "cymbal_or_hihat": high_energy / total,
            }
            token, spectral_share = max(shares.items(), key=lambda item: item[1])
            confidence = min(1.0, percussive_ratio * spectral_share * 2.0)
            results.append(
                UnpitchedDetection(
                    onset_id=onset.onset_id,
                    token=token,
                    confidence=confidence,
                )
            )
        return tuple(results)
