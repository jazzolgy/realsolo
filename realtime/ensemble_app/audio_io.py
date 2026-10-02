from __future__ import annotations

import queue
import time

from .audio_features import AudioFeatureExtractor


class AudioBackendUnavailable(RuntimeError):
    pass


def _sd():
    try:
        import sounddevice as sd
    except ImportError as exc:
        raise AudioBackendUnavailable(
            'Install audio support with: pip install -e ".[audio]"'
        ) from exc
    return sd


def list_audio_inputs() -> list[tuple[int, str, float]]:
    sd = _sd()
    result = []
    for index, info in enumerate(sd.query_devices()):
        if info.get("max_input_channels", 0) > 0:
            result.append((index, info["name"], float(info.get("default_samplerate", 0.0))))
    return result


def live_audio_poll(
    on_observation,
    on_tick,
    *,
    device: int | str | None = None,
    sample_rate: int = 48000,
    block_size: int = 1024,
    channels: int = 1,
    tick_s: float = 0.010,
) -> None:
    """Capture microphone PCM without doing analysis inside the audio callback."""

    sd = _sd()
    q: queue.SimpleQueue[tuple[float, object]] = queue.SimpleQueue()
    extractor = AudioFeatureExtractor(sample_rate=sample_rate)

    def callback(indata, frames, time_info, status):
        # Copy only; feature extraction stays outside the driver callback.
        q.put((time.monotonic(), indata[:, 0].copy()))

    with sd.InputStream(
        device=device,
        samplerate=sample_rate,
        blocksize=block_size,
        channels=channels,
        dtype="float32",
        callback=callback,
        latency="low",
    ):
        while True:
            handled = False
            while True:
                try:
                    timestamp, samples = q.get_nowait()
                except queue.Empty:
                    break
                obs = extractor.process(samples, timestamp)
                on_observation(obs)
                handled = True
            now = time.monotonic()
            on_tick(now)
            if not handled:
                time.sleep(tick_s)
