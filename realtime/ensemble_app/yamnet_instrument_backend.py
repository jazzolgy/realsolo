"""Actual pretrained instrument detector using Google YAMNet.

YAMNet is an AudioSet classifier (521 classes). RealSolo maps the subset of
AudioSet instrument/vocal classes relevant to the baseline instrument catalog
into the LearnedInstrumentBackend contract. Scores not represented by the
baseline catalog are left out rather than forced into the nearest instrument.

The model is loaded lazily from TensorFlow Hub and analyzes a rolling window so
the browser's small realtime PCM chunks are not classified in isolation.
"""
from __future__ import annotations

from collections import deque
import csv
from dataclasses import dataclass, field
from typing import Mapping


YAMNET_HANDLE="https://tfhub.dev/google/yamnet/1"
_TARGET_RATE=16000

# AudioSet display-name aliases -> RealSolo canonical instrument id.
# Matching is exact after lowercasing so generic Music/Speech classes do not
# accidentally become instrument evidence.
_AUDIOSET_TO_REALSOLO: dict[str,str]={
    "piano":"piano",
    "electric piano":"piano",
    "guitar":"guitar",
    "electric guitar":"guitar",
    "acoustic guitar":"guitar",
    "steel guitar, slide guitar":"guitar",
    "bass guitar":"electric_bass",
    "double bass":"acoustic_bass",
    "drum":"drums",
    "drum kit":"drums",
    "snare drum":"drums",
    "bass drum":"drums",
    "hi-hat":"drums",
    "cymbal":"drums",
    "saxophone":"saxophone",
    "trumpet":"trumpet",
    "flute":"flute",
    "singing":"vocal",
    "choir":"vocal",
    "vocal music":"vocal",
}


class YAMNetUnavailable(RuntimeError):
    pass


def _resample_linear(samples,src_rate:int,dst_rate:int):
    import numpy as np
    x=np.asarray(samples,dtype=np.float32).reshape(-1)
    if src_rate==dst_rate or x.size<2:
        return x.astype(np.float32,copy=False)
    out_n=max(1,int(round(x.size*dst_rate/src_rate)))
    src=np.linspace(0.0,1.0,num=x.size,endpoint=False,dtype=np.float64)
    dst=np.linspace(0.0,1.0,num=out_n,endpoint=False,dtype=np.float64)
    return np.interp(dst,src,x).astype(np.float32)


@dataclass
class YAMNetInstrumentBackend:
    """Rolling-window YAMNet backend for the RealSolo learned detector contract."""

    model_handle: str=YAMNET_HANDLE
    analysis_window_s: float=1.92
    min_window_s: float=.96
    _model: object | None=field(default=None,init=False,repr=False)
    _class_names: tuple[str,...]=field(default=(),init=False,repr=False)
    _buffers: dict[int,deque]=field(default_factory=dict,init=False,repr=False)
    _buffer_counts: dict[int,int]=field(default_factory=dict,init=False,repr=False)

    def _load(self) -> None:
        if self._model is not None:
            return
        try:
            import tensorflow_hub as hub
        except ImportError as exc:
            raise YAMNetUnavailable(
                'YAMNet requires: pip install -e ".[research-ml]"'
            ) from exc
        try:
            self._model=hub.load(self.model_handle)
            class_map_path=self._model.class_map_path().numpy().decode("utf-8")
            names=[]
            with open(class_map_path,newline="",encoding="utf-8") as fh:
                for row in csv.DictReader(fh):
                    names.append(str(row["display_name"]))
            self._class_names=tuple(names)
        except Exception as exc:
            self._model=None
            raise YAMNetUnavailable(f"could not load YAMNet: {exc}") from exc

    def _rolling_window(self,samples,*,sample_rate:int):
        import numpy as np
        x=np.asarray(samples,dtype=np.float32).reshape(-1)
        q=self._buffers.setdefault(sample_rate,deque())
        count=self._buffer_counts.get(sample_rate,0)
        if x.size:
            q.append(x.copy()); count+=x.size
        keep=max(1,int(round(self.analysis_window_s*sample_rate)))
        while q and count-len(q[0]) >= keep:
            count-=len(q.popleft())
        self._buffer_counts[sample_rate]=count
        if count < int(round(self.min_window_s*sample_rate)):
            return None
        joined=np.concatenate(tuple(q))
        if joined.size>keep:
            joined=joined[-keep:]
        return joined

    def predict(
        self,
        samples,
        *,
        sample_rate: int,
    ) -> tuple[Mapping[str,float],Mapping[str,float],Mapping[str,float]]:
        import numpy as np
        window=self._rolling_window(samples,sample_rate=sample_rate)
        if window is None:
            return {},{},{"yamnet_window_ready":0.0}

        self._load()
        waveform=_resample_linear(window,sample_rate,_TARGET_RATE)
        waveform=np.clip(waveform,-1.0,1.0).astype(np.float32,copy=False)
        scores,embeddings,_spectrogram=self._model(waveform)
        frame_scores=np.asarray(scores.numpy(),dtype=np.float32)
        if frame_scores.ndim!=2 or frame_scores.shape[1]!=len(self._class_names):
            raise YAMNetUnavailable("unexpected YAMNet score shape")
        mean_scores=frame_scores.mean(axis=0)

        merged: dict[str,float]={}
        for index,name in enumerate(self._class_names):
            target=_AUDIOSET_TO_REALSOLO.get(name.strip().lower())
            if target is None:
                continue
            # Multiple AudioSet subclasses can support the same RealSolo label.
            # Noisy-OR preserves convergent evidence without simple summation.
            p=max(0.0,min(1.0,float(mean_scores[index])))
            old=merged.get(target,0.0)
            merged[target]=1.0-(1.0-old)*(1.0-p)

        top=max(merged.values(),default=0.0)
        confidence={
            "yamnet_window_ready":1.0,
            "yamnet_instrument":top,
            "model":top,
        }
        # YAMNet is an event/instrument classifier, not a jazz-role classifier.
        # Role inference remains with the RealSolo baseline/context layers.
        return merged,{},confidence
