# RealSolo — Music Intelligence Platform

RealSolo is an AI musicianship research and development project.

The goal is not to precompose solos and replay them as improvisation. The AI Player must listen, understand form/harmony/phrase/ensemble context, prepare soft intentions and candidate families, commit only the immediately playable event, then listen and re-plan.

## Architecture

- `core/` — UMR, harmony, phrase, rhythm, cognition, legend profiles, online evaluator
- `players/` — instrument-specific performance grammars
- `realtime/` — audio/MIDI input, beat/form tracking, ensemble state, scheduler, output
- `research/` — legend studies and corpora
- `docs/` — architecture and project principles
- `tests/` — shared regression tests

## Workstreams

- `main` — integrated stable baseline
- `research/legend-intelligence` — shared jazz grammar + multi-legend research
- `player/piano` — AI pianist
- `realtime/ensemble-app` — live ensemble program

## Current baseline

v1.30 — Autonomous Legend Study + Online Improvisation Contract.

Key runtime rule: **Plan intention, not notes.**

Charlie Parker is the first high-resolution LegendProfile, not the identity of the model. The long-term system separates SharedJazzGrammar, era/substyle grammar, instrument grammar, LegendProfile, recording context, and current ensemble state.
