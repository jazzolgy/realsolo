"""Optional TorchScript backend for learned instrument probabilities.

Torch is imported lazily and is not added to the project's core dependencies.
The backend expects a model that maps a float tensor shaped [N, F] to either
class logits or class probabilities shaped [N, C].
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
from typing import Mapping, Sequence

from .learned_instrument import InstrumentFeatureVector


@dataclass
class TorchScriptInstrumentBackend:
    model_path: str
    class_labels: tuple[str, ...]
    output_is_logits: bool = True
    device: str = "cpu"
    backend_id: str = "torchscript-instrument:v0.1"

    def __post_init__(self) -> None:
        if not self.class_labels:
            raise ValueError("class_labels are required")
        if len(set(self.class_labels)) != len(self.class_labels):
            raise ValueError("class_labels must be unique")
        if not Path(self.model_path).exists():
            raise FileNotFoundError(self.model_path)
        self._model = None

    def _load_model(self):
        if self._model is not None:
            return self._model
        try:
            import torch
        except ImportError as exc:
            raise RuntimeError(
                "TorchScript instrument backend requires optional package 'torch'."
            ) from exc
        model = torch.jit.load(self.model_path, map_location=self.device)
        model.eval()
        self._model = model
        return model

    def predict_probabilities(
        self,
        features: Sequence[InstrumentFeatureVector],
    ) -> Sequence[Mapping[str, float]]:
        if not features:
            return ()
        feature_names = features[0].feature_names
        for item in features:
            item.validate()
            if item.feature_names != feature_names:
                raise ValueError(
                    "TorchScript backend requires consistent feature ordering"
                )

        try:
            import torch
        except ImportError as exc:
            raise RuntimeError(
                "TorchScript instrument backend requires optional package 'torch'."
            ) from exc

        model = self._load_model()
        tensor = torch.tensor(
            [item.values for item in features],
            dtype=torch.float32,
            device=self.device,
        )
        with torch.no_grad():
            output = model(tensor)

        if getattr(output, "ndim", None) != 2:
            raise ValueError("TorchScript model must return a rank-2 tensor")
        if int(output.shape[0]) != len(features):
            raise ValueError("TorchScript model returned wrong batch size")
        if int(output.shape[1]) != len(self.class_labels):
            raise ValueError("TorchScript model returned wrong class count")

        if self.output_is_logits:
            output = torch.softmax(output, dim=1)

        rows = output.detach().cpu().tolist()
        predictions: list[dict[str, float]] = []
        for row in rows:
            if any((not math.isfinite(float(value)) or float(value) < 0.0) for value in row):
                raise ValueError("TorchScript model returned invalid probabilities")
            total = sum(float(value) for value in row)
            if total <= 0.0:
                raise ValueError("TorchScript model returned zero probability mass")
            predictions.append(
                {
                    label: float(value) / total
                    for label, value in zip(self.class_labels, row)
                }
            )
        return tuple(predictions)
