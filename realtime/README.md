# Realtime — Live Ensemble App

This workstream owns input, timing/cue evidence, ensemble state, scheduling,
performance output and live diagnostics. Musical policy remains in Music
Intelligence Core.

## Current vertical slice

The current MIDI-first loop is:

```
performer MIDI
  -> chord-aware onset clustering
  -> adaptive beat/phase tracking
  -> phrase activity + space detection
  -> EnsembleState snapshot
  -> CoreImmediateBridge
  -> OnlineMusicalEvaluator / perform_one_event()
  -> generation-aware scheduler
  -> MIDI output
  -> listen again
```

The scheduler may cancel an unplayed future note when new performer evidence
arrives. Once a note-on has actually sounded, its note-off becomes mandatory
cleanup and cannot be invalidated by re-planning.

## Install

```bash
pip install -e ".[dev,midi]"
```

## Hardware smoke test

List ports:

```bash
realsolo-ensemble ports
```

Listen without generating notes:

```bash
realsolo-ensemble monitor --input "YOUR MIDI INPUT"
```

Closed-loop probe:

```bash
realsolo-ensemble probe --input "YOUR MIDI INPUT" --output "YOUR MIDI OUTPUT"
```

`probe` is deliberately **not** the final musical partner. It uses the shared
Core immediate-commit machinery but feeds it a diagnostic candidate set so we
can verify that RealSolo hears attacks, estimates pulse, detects phrase space,
commits one event, schedules it, and returns to listening. The diagnostic
response is an octave-down echo of the latest performer pitch after phrase-end
space.

The next musical layer should come from Core / instrument workstreams, not from
hard-coded accompaniment rules in `realtime`.
