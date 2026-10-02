# Stage-1 Audio Rendering

## Decision

Oscillators are a fallback only. The product rendering path is sample-based.

Current browser prototype:
- SpessaSynth `spessasynth_lib` 4.3.14
- SF2 / SF3 / SFOGG / DLS
- AudioWorklet synthesis
- scheduled note-on / note-off from RealSolo Performance Events

## Boundary

Music Intelligence does not choose a synthesizer waveform or sample file.
It emits performance intent:

```
pitch
velocity
duration
timing
role / instrument
articulation (future)
```

The renderer maps those events to an instrument backend.

## Current channel map

- 0 — piano
- 1 — acoustic bass
- 2 — tenor sax, temporary solo voice
- 9 — GM drums

## Product path

1. User-loadable SoundFont support (implemented).
2. Curated redistributable default bank.
3. Jazz-focused instrument banks:
   multi-velocity piano, upright bass, ride/hat/snare/kick.
4. Round robin / release / articulation metadata.
5. Dedicated expressive soloist renderer where ordinary GM multisamples become
   the limiting factor.

Do not couple Core logic to SoundFont program numbers. Program/channel mapping is
a renderer concern.
