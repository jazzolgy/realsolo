# Audio Evidence Engine Boundary

## Canonical name

The canonical subsystem name is **Audio Evidence Engine**.

The former name **Shared Audio Intelligence Engine** is deprecated because
"Intelligence" overlaps too strongly with the responsibility of the
Music Intelligence Core.

Recommended Python package:

```text
music_intelligence.audio_evidence
```

Recommended feature branch for the audio-side implementation:

```text
feature/audio-evidence-engine
```

## Responsibility split

### Audio Evidence Engine

Owns evidence about what was heard or observed:

- source separation;
- onset / offset detection;
- pitch and continuous-pitch evidence;
- timbre evidence;
- instrument probabilities;
- role probabilities when inferred from performance evidence;
- raw detector distributions;
- context-adjusted posterior distributions;
- uncertainty and alternatives;
- calibration;
- revision history;
- provenance;
- adapters from audio/MIDI analysis into Performance Evidence.

It does **not** own notation decisions or general musical reasoning.

### Music Intelligence Core

Owns shared musical semantics and instrument-neutral reasoning:

- harmony;
- form;
- phrase;
- ensemble state;
- interaction;
- tension / release;
- musical meaning;
- generic candidate reasoning.

### Performance Evidence

Performance Evidence is the stable contract between perception/evidence and
downstream musical interpretation.

```text
Audio / MIDI Source
        ↓
Audio Evidence Engine
        ↓
Performance Evidence
        ↓
Music Intelligence Core
        ↓
Transcription / Ensemble / Learning / Player
```

## Critical inference boundary

The following remain distinct:

```text
raw detector output
≠ context-adjusted posterior
≠ committed Performance Evidence
≠ musical meaning
≠ notation
```

Context adjustment inside the Audio Evidence Engine may use evidence that helps
interpret an observation, but it must preserve the original detector output and
correction provenance. It must not silently become a second copy of harmony,
form, or ensemble reasoning owned by the Music Intelligence Core.

## Package boundary

A new audio implementation should prefer a structure such as:

```text
src/music_intelligence/audio_evidence/
    adapters/
    detectors/
    observation/
    context/
    posterior/
    calibration/
    pipeline.py
```

The audio package should not directly edit or own:

- `transcribe/events.py`;
- notation interpretation;
- LogicalScore;
- engraving;
- MusicXML;
- learning admission;
- runtime prior policy.

If the Audio Evidence Engine needs a new field in Performance Evidence, it
should first define the adapter requirement, semantics, units, raw/posterior
status, optionality, confidence meaning, and provenance requirement. The shared
contract can then be extended additively.
