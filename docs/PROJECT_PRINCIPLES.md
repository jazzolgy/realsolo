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


## Constraint-aware creativity

RealSolo performers must remain capable of creative response in every musical context.

A constrained context does **not** mean creativity is disabled.

Examples:

- when the soloist is busy, creativity may move from density to timing, register,
  silence length, touch, or harmonic color restraint;
- when a vamp requires groove continuity, rhythm may stay stable while voicing,
  register, dynamics, articulation, omission, or color evolves;
- when another comping instrument occupies harmonic space, the pianist may create
  through sparse punctuation, register separation, rhythmic counter-shape, silence,
  texture, or response timing rather than duplicated harmony;
- near a form boundary, previously stable dimensions may loosen together to permit a
  new texture or role.

Therefore the system should not implement creativity as a random-temperature switch or
as a rule to maximize difference from the previous gesture.

The target is:

```
creative response
= musical coherence
+ context awareness
+ freedom on currently available dimensions
```

This remains subordinate to the runtime invariant:

```
Plan intention, not notes.
```

No creativity layer may freeze a future note sequence, voicing sequence, or comping
pattern.
