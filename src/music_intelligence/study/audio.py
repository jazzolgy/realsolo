"""Streaming local-audio front end for research study sessions.

This is deliberately a compact evidence extractor, not a transcription engine.
It never persists source audio. MP3/other formats are decoded through ffmpeg to
mono Float32 PCM and summarized into non-reconstructive window features.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from pathlib import Path
import shutil
import subprocess
from typing import Iterator


@dataclass(frozen=True)
class AudioWindowFeatures:
    start_s: float
    end_s: float
    rms: float
    peak: float
    zero_crossing_rate: float
    spectral_centroid_hz: float | None
    onset_rate_hz: float
    activity: float

    def validate(self)->None:
        if self.start_s < 0 or self.end_s <= self.start_s:
            raise ValueError("window must satisfy 0 <= start < end")
        if self.rms < 0 or self.peak < 0:
            raise ValueError("amplitude features may not be negative")
        if not 0.0 <= self.zero_crossing_rate <= 1.0:
            raise ValueError("zero_crossing_rate must be within 0..1")
        if self.spectral_centroid_hz is not None and self.spectral_centroid_hz < 0:
            raise ValueError("spectral centroid may not be negative")
        if self.onset_rate_hz < 0:
            raise ValueError("onset_rate_hz may not be negative")
        if not 0.0 <= self.activity <= 1.0:
            raise ValueError("activity must be within 0..1")


def _np():
    try:
        import numpy as np
    except ImportError as exc:
        raise RuntimeError('study audio requires: pip install -e ".[study]"') from exc
    return np


def _decode_process(path:Path,sample_rate:int,start_s:float):
    ffmpeg=shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError(
            "ffmpeg is required for the study MVP audio decoder; install ffmpeg and retry"
        )
    return subprocess.Popen(
        [
            ffmpeg,"-nostdin","-v","error","-ss",f"{start_s:.6f}","-i",str(path),
            "-f","f32le","-ac","1","-ar",str(sample_rate),"pipe:1",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _features(samples,start_s:float,sample_rate:int)->AudioWindowFeatures:
    np=_np()
    x=np.asarray(samples,dtype=np.float32).reshape(-1)
    if x.size < 2:
        raise ValueError("audio window is too short")
    rms=float(np.sqrt(np.mean(x*x,dtype=np.float64)))
    peak=float(np.max(np.abs(x)))
    zcr=float(np.mean((x[:-1] >= 0) != (x[1:] >= 0)))

    nfft=1
    while nfft < min(x.size,8192):
        nfft*=2
    nfft=max(256,nfft)
    frame=x[:min(x.size,nfft)]
    if frame.size<nfft:
        frame=np.pad(frame,(0,nfft-frame.size))
    mag=np.abs(np.fft.rfft(frame*np.hanning(nfft)))
    freqs=np.fft.rfftfreq(nfft,d=1.0/sample_rate)
    denom=float(mag.sum())
    centroid=float((mag*freqs).sum()/denom) if denom>1e-12 else None

    # Local energy attacks: enough for navigation/activity evidence while
    # remaining explicitly weaker than a learned onset/transcription model.
    frame_n=max(128,int(round(.025*sample_rate)))
    hop=max(64,int(round(.010*sample_rate)))
    energies=[]
    for i in range(0,max(1,x.size-frame_n+1),hop):
        f=x[i:i+frame_n]
        if f.size<frame_n:
            break
        energies.append(float(np.sqrt(np.mean(f*f,dtype=np.float64))))
    onset_count=0
    if len(energies)>=3:
        e=np.asarray(energies,dtype=np.float64)
        diff=np.maximum(0.0,np.diff(e))
        threshold=float(np.median(diff)+2.5*np.median(np.abs(diff-np.median(diff))))
        threshold=max(threshold,0.003)
        onset_count=int(np.sum(diff>threshold))
    duration=x.size/sample_rate
    onset_rate=onset_count/max(duration,1e-9)

    # Bounded loudness/activity proxy; not a semantic density label.
    activity=max(0.0,min(1.0,rms/.12))
    out=AudioWindowFeatures(
        start_s=start_s,
        end_s=start_s+duration,
        rms=rms,
        peak=peak,
        zero_crossing_rate=zcr,
        spectral_centroid_hz=centroid,
        onset_rate_hz=float(onset_rate),
        activity=activity,
    )
    out.validate()
    return out


def stream_audio_windows(
    audio_path:str|Path,
    *,
    sample_rate:int=16000,
    window_s:float=2.0,
    hop_s:float=1.0,
    start_s:float=0.0,
    max_seconds:float|None=None,
)->Iterator[AudioWindowFeatures]:
    """Decode and yield overlapping compact feature windows.

    Source PCM is transient. The generator yields summaries only.
    """
    if sample_rate<=0 or window_s<=0 or hop_s<=0:
        raise ValueError("sample_rate/window_s/hop_s must be positive")
    if hop_s>window_s:
        raise ValueError("hop_s may not exceed window_s")
    if start_s<0:
        raise ValueError("start_s may not be negative")
    path=Path(audio_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(path)

    np=_np()
    proc=_decode_process(path,sample_rate,start_s)
    assert proc.stdout is not None
    window_n=max(2,int(round(window_s*sample_rate)))
    hop_n=max(1,int(round(hop_s*sample_rate)))
    chunk_bytes=max(4096,hop_n*4)
    buffer=np.empty(0,dtype=np.float32)
    start_sample=0
    emitted=0
    try:
        while True:
            raw=proc.stdout.read(chunk_bytes)
            if raw:
                usable=len(raw)-(len(raw)%4)
                if usable:
                    x=np.frombuffer(raw[:usable],dtype="<f4").astype(np.float32,copy=True)
                    buffer=np.concatenate((buffer,x))
            while buffer.size>=window_n:
                relative_s=start_sample/sample_rate
                if max_seconds is not None and relative_s>=max_seconds:
                    return
                yield _features(buffer[:window_n],start_s+relative_s,sample_rate)
                buffer=buffer[hop_n:]
                start_sample+=hop_n
                emitted+=1
            if not raw:
                break
        if emitted==0 and buffer.size>=2:
            yield _features(buffer,start_s,sample_rate)
    finally:
        try:
            proc.stdout.close()
        except Exception:
            pass
        if proc.poll() is None:
            proc.terminate()
        proc.wait(timeout=5)
        if proc.returncode not in (0,-15):
            stderr=b""
            if proc.stderr is not None:
                stderr=proc.stderr.read()
            raise RuntimeError(
                "ffmpeg decode failed: "+stderr.decode("utf-8","replace")[-1000:]
            )
