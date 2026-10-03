# Project Principles

## Identity

RealSolo is a Music Intelligence Platform. The AI Player is an ensemble musician that listens, interprets context, performs, listens again, and adapts.

## Non-negotiable runtime improvisation rule

The AI must not precompose a complete performance and replay it as if improvised.

It may:
- know the form and future harmony
- maintain a musical narrative
- form intentions and soft targets
- prepare candidate families

It must:
- keep exact note-level decisions open until commitment time
- evaluate the current ensemble state
- commit only immediately playable events
- never rewrite a note after it has sounded
- recover/reinterpret through subsequent performance

**Plan intention, not notes.**

## Multi-Legend intelligence

No single legend defines the model.

Deep studies of Charlie Parker and later masters are stored as contextual tendencies rather than copied performances. The architecture separates:

- SharedJazzGrammar
- Era / Substyle Grammar
- Instrument Grammar
- LegendProfile
- RecordingContextProfile
- Current Ensemble State

Legend knowledge is mixed at candidate-policy level, not by literal phrase splicing.

## Shared representation

UMR is the common internal representation across:
- AI Player
- Transcriber
- analysis/research
- composition/education applications

Performance representation and notation representation remain separate.

## Human role

The user is Musical Director / Domain Expert, not the routine debugger of every bar. Repeated expert corrections should be converted into reusable tests, priors, evaluators, and corpus annotations.

## Workstream contract

The three active workstreams are:
1. Legend Intelligence / Core
2. AI Pianist
3. Live Ensemble App

Each uses one shared repository and avoids silently forking the shared musical architecture.


## Canonical musical coordinate

RealSolo treats form/section/form-iteration/bar/beat/subdivision as the
canonical semantic coordinate for learning and reasoning. Absolute audio time
is retained as provenance and alignment evidence, not as the primary musical
address.

Temporary estimates such as `bar_est` must be promoted through beat/bar/form
alignment before becoming final shared-learning keys. Structural
interpretations such as phrase position, harmonic function, cadence position,
motif state, role, and ensemble state remain separate from the coordinate so
their confidence and provenance can be tracked independently.

See `docs/CANONICAL_MUSICAL_COORDINATE_POLICY.md`.
