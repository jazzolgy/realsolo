# UMR v1.41 — Harmonic Reasoning Orchestrator

## Purpose

v1.34–v1.40 built the principal shared harmony components separately. v1.41
connects them into one current-moment reasoning pass.

This is integration, not a new harmony textbook.

## Pipeline

HarmonicFrame
-> competing HarmonicHypotheses
-> ModalState / LocalKeyHypothesis
-> Contextual Tension
-> Voice-Leading state / ResolutionDebt
-> Reharmonization proposals
-> base HarmonicAffordances
-> ranked current HarmonicActionOptions

The specialist modules remain independently testable and auditable.

## Inputs remain separated

Expected, Observed, and Inferred harmony are still stored separately in
HarmonicFrame. Multiple HarmonicHypotheses can remain active.

The orchestrator does not erase ambiguity. Under high ambiguity it modestly
favours reversible/cross-compatible actions such as connection, stabilization,
or anticipation and dampens premature intensification or reharmonization.

## HarmonicActionOption

An option is an instrument-neutral action family, not a note sequence.

It contains:
- source affordance/proposal ID
- intent
- harmonic role
- current weight
- confidence
- compatibility with active interpretations
- context tags
- reasons

Examples of action families:
- preserve dominant identity
- connect toward structural target
- intensify with contextual tension
- anticipate known next harmony
- consider one reharmonization proposal
- controlled outside/return

Piano, bass, saxophone, horns, or other players realize these differently.

## Context composition

v1.41 can allow current action weights to respond to:
- harmonic interpretation ambiguity
- modal-anchor strength
- local-key / tonicization evidence
- active tension resolution pressure
- voice-leading resolution debt
- reharmonization continuity

The numeric weights are provisional shared heuristics. They should later be
replaced or calibrated by corpus statistics, expert annotation, pairwise
preference, and performance evaluation.

## Runtime invariant

The orchestrator does not output:
- future note sequences
- fixed future chord sequences
- piano voicings
- bass lines
- drum patterns

It only scores current harmonic action families.

Perceive
-> update harmonic evidence
-> maintain competing interpretations
-> compose shared harmonic context
-> produce current affordances
-> instrument generates current candidates
-> commit one immediate action
-> listen/re-plan.
