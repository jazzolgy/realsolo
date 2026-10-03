#!/usr/bin/env python3
"""Deterministic offline event extraction for RealSolo Shared Audio Intelligence.

This script creates hypothesis-level evidence from owner-supplied audio. It does
not claim ground-truth transcription or final instrument ownership.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import librosa
import numpy as np
from scipy.signal import find_peaks

SR = 22050
HOP = 512
N_FFT = 4096
TRACK_START = 708.0
TRACK_END = 1069.0
PITCH_PEAK_THRESHOLD = 0.18
MAX_PITCHES_PER_ONSET = 6
HARMONIC_ONSET_DELTA = 0.05
PERCUSSIVE_ONSET_DELTA = 0.12


def sha256_file(path: Path, chunk: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        while True:
            block = f.read(chunk)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def midi_name(midi: float) -> str:
    n = int(round(midi))
    names = ('C','C#','D','D#','E','F','F#','G','G#','A','A#','B')
    return f"{names[n % 12]}{n // 12 - 1}"


def normalize(d: dict[str, float]) -> dict[str, float]:
    total = sum(max(0.0, float(v)) for v in d.values())
    return {k: max(0.0, float(v)) / total for k, v in d.items()} if total else d


def instrument_prior(midi: float, centroid_hz: float) -> dict[str, float]:
    if midi < 45:
        base = {'bass': .76, 'piano_lh': .18, 'piano_rh': .01, 'other': .05}
    elif midi < 55:
        base = {'bass': .55, 'piano_lh': .35, 'piano_rh': .03, 'other': .07}
    elif midi < 64:
        base = {'bass': .25, 'piano_lh': .52, 'piano_rh': .15, 'other': .08}
    elif midi < 76:
        base = {'bass': .05, 'piano_lh': .30, 'piano_rh': .58, 'other': .07}
    else:
        base = {'bass': .01, 'piano_lh': .08, 'piano_rh': .84, 'other': .07}
    if centroid_hz > 2600 and midi < 60:
        base['other'] += .08
        base['bass'] *= .92
        base['piano_lh'] *= .92
    return normalize(base)


def role_prior(midi: float) -> dict[str, float]:
    if midi < 55:
        return normalize({'time_floor': .48, 'harmonic_support': .32, 'counterline': .15, 'other': .05})
    if midi < 70:
        return normalize({'harmonic_support': .45, 'foreground_line': .25, 'response': .20, 'other': .10})
    return normalize({'foreground_line': .58, 'response': .22, 'harmonic_support': .12, 'other': .08})


def beat_position_for_time(t: float, beat_times: np.ndarray, beat_period: float) -> float:
    if len(beat_times) < 2:
        return t / beat_period
    beat_idx = np.arange(len(beat_times), dtype=float)
    if t < beat_times[0]:
        return (t - beat_times[0]) / beat_period
    if t > beat_times[-1]:
        return beat_idx[-1] + (t - beat_times[-1]) / beat_period
    return float(np.interp(t, beat_times, beat_idx))


def duration_from_peak(S: np.ndarray, bin_idx: int, frame: int, peak_mag: float) -> float:
    max_frames = int(round(1.5 * SR / HOP))
    stop = min(S.shape[1] - 1, frame + max_frames)
    threshold = peak_mag * .25
    end = frame + 1
    for j in range(frame + 1, stop + 1):
        lo = max(0, bin_idx - 1)
        hi = min(S.shape[0], bin_idx + 2)
        if float(np.max(S[lo:hi, j])) < threshold:
            break
        end = j
    return max(HOP / SR, (end - frame + 1) * HOP / SR)


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def analyze(audio_path: Path, out_dir: Path) -> dict:
    duration = TRACK_END - TRACK_START
    y, sr = librosa.load(audio_path, sr=SR, mono=True, offset=TRACK_START, duration=duration)
    if sr != SR:
        raise RuntimeError('unexpected sample rate')

    harmonic, percussive = librosa.effects.hpss(y)

    harm_env = librosa.onset.onset_strength(y=harmonic, sr=sr, hop_length=HOP)
    harm_frames = librosa.onset.onset_detect(
        onset_envelope=harm_env, sr=sr, hop_length=HOP, units='frames',
        normalize=True, delta=HARMONIC_ONSET_DELTA, wait=1,
    )
    perc_env = librosa.onset.onset_strength(y=percussive, sr=sr, hop_length=HOP)
    perc_frames = librosa.onset.onset_detect(
        onset_envelope=perc_env, sr=sr, hop_length=HOP, units='frames',
        normalize=True, delta=PERCUSSIVE_ONSET_DELTA, wait=1,
    )

    tempo_arr, beat_frames = librosa.beat.beat_track(
        y=percussive, sr=sr, hop_length=HOP, units='frames'
    )
    tempo = float(np.atleast_1d(tempo_arr)[0])
    beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=HOP)
    beat_period = float(np.median(np.diff(beat_times))) if len(beat_times) > 1 else 60.0 / tempo

    S_h = np.abs(librosa.stft(harmonic, n_fft=N_FFT, hop_length=HOP, window='hann', center=True))
    S_p = np.abs(librosa.stft(percussive, n_fft=N_FFT, hop_length=HOP, window='hann', center=True))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=N_FFT)
    pitch_bins = np.where((freqs >= 40.0) & (freqs <= 5000.0))[0]

    centroid = librosa.feature.spectral_centroid(y=y, sr=sr, n_fft=N_FFT, hop_length=HOP)[0]
    rms = librosa.feature.rms(y=y, frame_length=N_FFT, hop_length=HOP)[0]
    rms95 = max(1e-9, float(np.percentile(rms, 95)))
    harm95 = max(1e-9, float(np.percentile(harm_env, 95)))
    perc95 = max(1e-9, float(np.percentile(perc_env, 95)))

    pitch_rows: list[dict] = []
    event_counter = 0
    for onset_index, frame in enumerate(harm_frames):
        if frame >= S_h.shape[1]:
            continue
        spectrum = S_h[:, frame]
        seg = spectrum[pitch_bins]
        peaks, _ = find_peaks(seg, distance=2)
        if not len(peaks):
            continue
        values = seg[peaks]
        mx = float(values.max())
        selected = peaks[values >= PITCH_PEAK_THRESHOLD * mx]
        selected = selected[np.argsort(seg[selected])[::-1]][:MAX_PITCHES_PER_ONSET]
        if not len(selected):
            continue

        t = float(librosa.frames_to_time(frame, sr=sr, hop_length=HOP))
        source_t = TRACK_START + t
        beat_pos = beat_position_for_time(t, beat_times, beat_period)
        bar = math.floor(max(0.0, beat_pos) / 4.0) + 1
        beat_in_bar = max(0.0, beat_pos) % 4.0 + 1.0
        onset_conf = min(1.0, float(harm_env[min(frame, len(harm_env)-1)]) / harm95)
        dyn = min(1.0, float(rms[min(frame, len(rms)-1)]) / rms95)
        cent = float(centroid[min(frame, len(centroid)-1)])
        polyphony = len(selected)

        for rank, local_peak in enumerate(selected, start=1):
            bin_idx = int(pitch_bins[local_peak])
            freq = float(freqs[bin_idx])
            midi = float(librosa.hz_to_midi(freq))
            peak_mag = float(spectrum[bin_idx])
            local_floor = float(np.median(seg)) + 1e-12
            snr_like = peak_mag / local_floor
            spectral_conf = min(1.0, max(0.0, (math.log10(max(1.0, snr_like)) / 2.0)))
            duration_s = duration_from_peak(S_h, bin_idx, int(frame), peak_mag)
            inst = instrument_prior(midi, cent)
            roles = role_prior(midi)
            event_counter += 1
            pitch_rows.append({
                'event_id': f'BE-003:pitch:{event_counter:05d}',
                'onset_group_id': f'BE-003:onset:{onset_index+1:04d}',
                'relative_time_s': f'{t:.6f}',
                'source_time_s': f'{source_t:.6f}',
                'beat_position_est': f'{beat_pos:.6f}',
                'bar_est': bar,
                'beat_in_bar_est': f'{beat_in_bar:.6f}',
                'pitch_midi': f'{midi:.4f}',
                'note_name_nearest': midi_name(midi),
                'frequency_hz': f'{freq:.4f}',
                'duration_s_est': f'{duration_s:.6f}',
                'spectral_confidence': f'{spectral_conf:.6f}',
                'onset_confidence': f'{onset_conf:.6f}',
                'duration_confidence': f'{min(.85, .35 + .5*spectral_conf):.6f}',
                'instrument_confidence': f'{max(inst.values()):.6f}',
                'alignment_confidence': '',
                'dynamic_proxy': f'{dyn:.6f}',
                'spectral_centroid_hz': f'{cent:.3f}',
                'polyphony_at_onset': polyphony,
                'peak_rank': rank,
                'bass_p': f"{inst['bass']:.6f}",
                'piano_lh_p': f"{inst['piano_lh']:.6f}",
                'piano_rh_p': f"{inst['piano_rh']:.6f}",
                'other_instrument_p': f"{inst['other']:.6f}",
                'time_floor_role_p': f"{roles.get('time_floor',0.0):.6f}",
                'harmonic_support_role_p': f"{roles.get('harmonic_support',0.0):.6f}",
                'foreground_line_role_p': f"{roles.get('foreground_line',0.0):.6f}",
                'response_role_p': f"{roles.get('response',0.0):.6f}",
                'status': 'NOTE_HYPOTHESIS',
                'provenance': 'shared_audio_intelligence_v0_2;spectral_peak;owner_supplied_audio',
            })

    perc_rows: list[dict] = []
    low_mask = (freqs >= 30) & (freqs < 180)
    mid_mask = (freqs >= 180) & (freqs < 2200)
    high_mask = (freqs >= 2200) & (freqs <= 10000)
    for i, frame in enumerate(perc_frames, start=1):
        if frame >= S_p.shape[1]:
            continue
        spectrum = S_p[:, frame]
        low = float(np.sum(spectrum[low_mask]**2))
        mid = float(np.sum(spectrum[mid_mask]**2))
        high = float(np.sum(spectrum[high_mask]**2))
        total = max(1e-12, low + mid + high)
        lr, mr, hr = low/total, mid/total, high/total
        if hr >= .58:
            cls = 'cymbal_or_hi_hat'
            cp = hr
        elif lr >= .40:
            cls = 'kick_or_low_percussion'
            cp = lr
        elif mr >= .50:
            cls = 'snare_or_mid_percussion'
            cp = mr
        else:
            cls = 'unresolved_percussive_event'
            cp = max(lr, mr, hr)
        t = float(librosa.frames_to_time(frame, sr=sr, hop_length=HOP))
        beat_pos = beat_position_for_time(t, beat_times, beat_period)
        bar = math.floor(max(0.0, beat_pos) / 4.0) + 1
        beat_in_bar = max(0.0, beat_pos) % 4.0 + 1.0
        onset_conf = min(1.0, float(perc_env[min(frame, len(perc_env)-1)]) / perc95)
        perc_rows.append({
            'event_id': f'BE-003:perc:{i:05d}',
            'relative_time_s': f'{t:.6f}',
            'source_time_s': f'{TRACK_START+t:.6f}',
            'beat_position_est': f'{beat_pos:.6f}',
            'bar_est': bar,
            'beat_in_bar_est': f'{beat_in_bar:.6f}',
            'low_energy_ratio': f'{lr:.6f}',
            'mid_energy_ratio': f'{mr:.6f}',
            'high_energy_ratio': f'{hr:.6f}',
            'drum_class_hypothesis': cls,
            'class_confidence': f'{cp:.6f}',
            'onset_confidence': f'{onset_conf:.6f}',
            'status': 'EVENT_HYPOTHESIS',
            'provenance': 'shared_audio_intelligence_v0_2;percussive_hpss;owner_supplied_audio',
        })

    beat_rows = []
    for i, (fr, t) in enumerate(zip(beat_frames, beat_times), start=1):
        beat_rows.append({
            'beat_index_est': i,
            'relative_time_s': f'{float(t):.6f}',
            'source_time_s': f'{TRACK_START+float(t):.6f}',
            'bar_est': (i-1)//4 + 1,
            'beat_in_bar_est': (i-1)%4 + 1,
            'canonical_alignment_status': 'UNRESOLVED',
        })

    out_dir.mkdir(parents=True, exist_ok=True)
    pitch_fields = list(pitch_rows[0].keys()) if pitch_rows else []
    chunk_size = 2000
    pitch_files = []
    for start in range(0, len(pitch_rows), chunk_size):
        part = start // chunk_size + 1
        p = out_dir / f'pitch_hypotheses_part_{part:02d}.csv'
        write_csv(p, pitch_rows[start:start+chunk_size], pitch_fields)
        pitch_files.append({'file': p.name, 'rows': len(pitch_rows[start:start+chunk_size])})
    write_csv(out_dir/'percussive_events.csv', perc_rows, list(perc_rows[0].keys()))
    write_csv(out_dir/'beat_grid.csv', beat_rows, list(beat_rows[0].keys()))

    inst_ambiguous = 0
    for row in pitch_rows:
        probs = sorted([float(row['bass_p']), float(row['piano_lh_p']), float(row['piano_rh_p']), float(row['other_instrument_p'])], reverse=True)
        if probs[0] < .70 or probs[0]-probs[1] < .15:
            inst_ambiguous += 1

    class_counts: dict[str,int] = {}
    for row in perc_rows:
        class_counts[row['drum_class_hypothesis']] = class_counts.get(row['drum_class_hypothesis'],0)+1

    metadata = {
        'schema': 'realsolo.shared_audio_intelligence.event_dataset.v0.2',
        'source_id': 'BE-003',
        'title': 'Autumn Leaves',
        'source_family': 'be_playlist_project_audio',
        'source_filename': audio_path.name,
        'source_sha256': sha256_file(audio_path),
        'track_window_s': {'start': TRACK_START, 'end': TRACK_END, 'duration': duration},
        'training_rights_disposition': 'DERIVED_ONLY',
        'publication_class': 'PUBLIC_DERIVED',
        'analysis_method': {
            'sample_rate': SR, 'hop_length': HOP, 'n_fft': N_FFT,
            'hpss': 'librosa.effects.hpss default',
            'harmonic_onset_delta': HARMONIC_ONSET_DELTA,
            'percussive_onset_delta': PERCUSSIVE_ONSET_DELTA,
            'pitch_peak_threshold_relative_to_onset_max': PITCH_PEAK_THRESHOLD,
            'max_pitch_hypotheses_per_onset': MAX_PITCHES_PER_ONSET,
        },
        'counts': {
            'harmonic_onsets': int(len(harm_frames)),
            'pitch_hypotheses': int(len(pitch_rows)),
            'percussive_events': int(len(perc_rows)),
            'beat_positions': int(len(beat_rows)),
            'ambiguous_instrument_hypotheses': int(inst_ambiguous),
        },
        'tempo_bpm_estimate': tempo,
        'percussive_class_counts': class_counts,
        'pitch_files': pitch_files,
        'files': {
            'percussive_events': 'percussive_events.csv',
            'beat_grid': 'beat_grid.csv',
        },
        'interpretation_limits': [
            'pitch rows are spectral NOTE_HYPOTHESES, not confirmed notes',
            'instrument probabilities are conservative acoustic/register priors, not final ownership',
            'bar numbers are audio-grid estimates, not canonical score bars',
            'canonical score/form alignment remains unresolved',
        ],
    }
    (out_dir/'metadata.json').write_text(json.dumps(metadata, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    return metadata


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('audio')
    ap.add_argument('out_dir')
    args = ap.parse_args()
    meta = analyze(Path(args.audio), Path(args.out_dir))
    print(json.dumps(meta, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
