# UMR v1.43 — Shared Ensemble State

## Purpose

The next integration problem is ensemble coordination.

Piano, bass, drums, and saxophone must not behave like four independent
generators playing at the same time. They need a common live state that lets
each player hear the others' current musical intentions and recent actions.

v1.43 defines that common contract.

## Shared state

EnsembleState contains:
- transport / form location;
- active player roster and roles;
- short-lived PlayerActionIntent messages;
- recent InteractionEvents;
- reference to current shared harmonic state;
- aggregate density / energy / tension;
- estimated space available;
- current leader hypothesis;
- monotonic generation counter.

This is coordination state, not a score.

## PlayerActionIntent

Each player may publish a small semantic message describing its current action
or immediate intention:
- interaction kind;
- provisional / committed / played state;
- density;
- energy;
- tension;
- space request;
- leadership;
- phrase maturity;
- optional target players;
- semantic tags;
- decision / commit time;
- provenance.

Exact pitches, voicings, bass lines, or drum patterns remain inside the
player-specific committed event and renderer.

## Interaction vocabulary

Initial shared interaction kinds:
- lead / follow / answer;
- support / yield;
- build / punctuate / setup;
- lock;
- contrast;
- hold space;
- transition.

This vocabulary is intentionally instrument-neutral.

## Player view

Every player reads the same EnsembleState but receives a self-filtered
PlayerEnsembleView containing the other players' intents, shared aggregate
activity, leadership, and interaction history.

Examples:
- sax density rises -> piano can yield;
- drums build -> bass can lock rather than over-decorate;
- sax phrase maturity approaches ending -> piano/drums may prepare response;
- piano fill becomes active -> sax can hold space;
- strong leader signal -> supporting players can reduce competing leadership.

These are future policy examples; v1.43 defines the state contract, not all
behaviour rules.

## Realtime app

The realtime app should own the authoritative transport clock and shared state
instance. Each player receives a snapshot, evaluates one immediate action,
publishes its intent/commitment, and returns control.

The target loop is:

audio / chart / transport
-> update UMR + harmony
-> update EnsembleState
-> distribute snapshot to players
-> player candidate evaluation
-> interaction scheduler
-> commit immediate actions
-> render
-> ingest what happened
-> update EnsembleState
-> repeat.

## Causality

Already-played actions remain immutable.

PlayerActionIntent may be provisional and revised before commitment. Once
committed/played, later ensemble input can only influence subsequent actions.

This is the foundation for the first AI trio test (piano + bass + drums) and
later quartet test with saxophone.
