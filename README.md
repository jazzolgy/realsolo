# RealSolo — Music Intelligence Platform

RealSolo is an AI musicianship research and development project.

The long-term product is a **Music Intelligence Platform**, not only an AI improviser. The shared Music Intelligence Core should support multiple applications while preserving a common musical representation, reasoning, learning and memory layer.

## Platform applications

- **AI Player** — listens, understands form/harmony/phrase/ensemble context, prepares soft intentions and candidate families, commits only the immediately playable event, then listens and re-plans.
- **AI Transcriber / Notation** — converts performed or generated musical evidence into readable, editable, playable scores.
- **Composition Assistant** — future composition and arranging support built on the same musical intelligence.
- **Practice & Education** — future practice, feedback and learning applications.
- **Research & Analysis** — corpus, style, legend, interaction and music-intelligence research.

The notation engine is a **shared platform capability with a product-independent boundary**. It must be usable inside RealSolo, while remaining separable enough to become an independent commercial application later without rewriting the musical core.

## Architecture

- `core/` and `src/music_intelligence/` — UMR, harmony, phrase, rhythm, cognition, learning, memory, vocabulary, legend profiles and online evaluator
- `players/` — instrument-specific performance grammars and realization
- `realtime/` — low-latency audio/MIDI input, tracking, scheduling and output
- `transcribe/` / notation engine workstream — performance evidence → notation intelligence → logical score → engraving/layout → MusicXML / renderer
- `research/` — legend studies and corpora
- `docs/` — architecture and project principles
- `tests/` — shared regression tests

See `docs/PLATFORM_ARCHITECTURE.md` and `docs/NOTATION_ENGINE_BOUNDARY.md`.

## Workstreams

- `main` — integrated stable baseline
- `research/legend-intelligence` — shared jazz grammar + multi-legend research
- `player/piano` — AI pianist
- `realtime/ensemble-app` — live ensemble program
- `transcribe` — AI transcription / notation workstream; must remain portable enough for future standalone product extraction

## Current baseline

v1.30 — Autonomous Legend Study + Online Improvisation Contract.

Key runtime rule: **Plan intention, not notes.**

Charlie Parker is the first high-resolution LegendProfile, not the identity of the model. The long-term system separates SharedJazzGrammar, era/substyle grammar, instrument grammar, LegendProfile, recording context, and current ensemble state.
