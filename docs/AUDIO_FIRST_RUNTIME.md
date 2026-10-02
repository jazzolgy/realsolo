# Audio-First Runtime Contract

## Product requirement

RealSolo is not a MIDI accompaniment application.

The primary product case is a musician playing a real acoustic or amplified
instrument while a phone/tablet microphone listens. MIDI remains an optional,
high-precision parallel source.

## Layer boundary

### Device audio layer

A platform-specific adapter owns:
- microphone permission
- audio session / route
- sample rate and buffer duration
- timestamps
- PCM delivery
- interruption / route-change handling

Examples:
- iOS: AVAudioSession + AVAudioEngine/Core Audio
- Android: low-latency native audio path
- desktop development: PortAudio via sounddevice

It must not own musical policy.

### Causal perception layer

PCM frames become timestamped evidence:
- RMS / peak
- onset strength + onset event
- pitch estimate + confidence
- later: multi-pitch / chord evidence
- later: timbre / articulation
- later: source/role evidence

The important distinction is **evidence vs meaning**. A detected transient is
not automatically a beat or cue. Core and ensemble tracking interpret it in
context.

### Ensemble layer

AudioObservation and MidiObservation converge before musical decision making.
This lets the same beat, phrase, cue, form and interaction state operate with:
- microphone only
- MIDI only
- hybrid audio + MIDI

## Latency rule

The microphone callback must do the minimum possible work: copy/queue PCM and
return. Feature extraction and model inference happen outside the hardware
callback. Future neural perception adapters must obey the same rule.

## Current baseline

The first audio implementation intentionally uses lightweight DSP:
- spectral-flux onset evidence
- RMS / peak energy
- bounded normalized-autocorrelation pitch evidence

These are replaceable baselines, not claims of solved polyphonic MIR. Their job
is to let us exercise the whole live architecture now while preserving an
interface for stronger learned models later.

## Next perception milestones

1. Robust piano/onset model under phone-mic room acoustics.
2. Polyphonic pitch/chroma and observed-harmony evidence.
3. Beat/downbeat tracker that fuses onset, harmonic rhythm and prior form.
4. Cue evidence for count-in, pickup, rubato convergence, break and ending.
5. Instrument/timbre/role estimation where useful.
6. Mobile-native low-latency audio implementation.
