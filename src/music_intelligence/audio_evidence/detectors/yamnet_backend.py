"""Optional YAMNet backend for coarse pretrained instrument priors.

YAMNet is an AudioSet classifier, not a note-level ownership model. Its frame
scores are aligned to detector onsets and used only as weak prior evidence.
TensorFlow / TensorFlow Hub are imported lazily.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from typing import Sequence

from ..adapters.source import AudioSource
from .audioset_prior import AudioSetFrameScores
from .contracts import OnsetDetection
from .librosa_baseline import LibrosaSourceLoader


@dataclass
class YAMNetAudioSetBackend:
    model_url: str = "https://tfhub.dev/google/yamnet/1"
    frame_hop_seconds: float = 0.48
    backend_id: str = "yamnet-audioset:v0.1"

    def __post_init__(self) -> None:
        if self.frame_hop_seconds <= 0.0:
            raise ValueError("frame_hop_seconds must be positive")
        self._model = None
        self._class_names = None
        self._loader = LibrosaSourceLoader(sample_rate=16000, mono=True)

    def _load(self):
        if self._model is not None:
            return self._model, self._class_names
        try:
            import tensorflow as tf
            import tensorflow_hub as hub
        except ImportError as exc:
            raise RuntimeError(
                "YAMNet backend requires optional packages "
                "'tensorflow' and 'tensorflow_hub'."
            ) from exc

        model = hub.load(self.model_url)
        class_map_path = model.class_map_path().numpy()
        if isinstance(class_map_path, bytes):
            class_map_path = class_map_path.decode("utf-8")

        class_names: list[str] = []
        with tf.io.gfile.GFile(class_map_path) as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                class_names.append(row["display_name"])

        self._model = model
        self._class_names = tuple(class_names)
        return self._model, self._class_names

    def score_onsets(
        self,
        source: AudioSource,
        onsets: Sequence[OnsetDetection],
    ) -> Sequence[AudioSetFrameScores]:
        if not onsets:
            return ()
        model, class_names = self._load()
        decoded = self._loader.load(source)

        scores, _, _ = model(decoded.samples)
        rows = scores.numpy()

        results: list[AudioSetFrameScores] = []
        for onset in onsets:
            onset.validate()
            relative = onset.onset_seconds - decoded.source_offset_seconds
            frame_index = int(round(max(relative, 0.0) / self.frame_hop_seconds))
            frame_index = max(0, min(frame_index, len(rows) - 1))
            row = rows[frame_index]
            results.append(
                AudioSetFrameScores(
                    onset_id=onset.onset_id,
                    scores={
                        label: float(score)
                        for label, score in zip(class_names, row)
                    },
                )
            )
        return tuple(results)
