# UMR v1.44 — Interaction Scheduler

## Purpose

v1.43 gave every player a shared EnsembleState. v1.44 turns that state into
short-lived coordination directives.

The scheduler answers questions such as:
- who should lead right now?
- who should yield?
- is there a phrase-handoff window?
- should drums set up the next event?
- should bass lock the floor?
- is the ensemble too dense?
- is there enough space for another foreground action?
- are we approaching a form boundary?

It does **not** compose the ensemble.

## Output

Each player receives one InteractionDirective containing:
- interaction kind;
- optional target player(s);
- density adjustment;
- energy adjustment;
- leadership adjustment;
- space priority;
- confidence;
- reasons;
- context tags.

The directive modifies player candidate policy; it never supplies exact notes,
voicings, bass lines, or drum patterns.

## Initial interaction policy

The first policy is intentionally small and interpretable.

### Active leader

When another player has strong leadership:
- comping / secondary melody tends to YIELD;
- bass tends to LOCK;
- drums tend to SUPPORT.

### Phrase handoff

When a leader reaches high phrase maturity:
- drums may SETUP;
- piano/support roles may ANSWER;
- another melody/solo role may ANSWER rather than overlap;
- bass tends to preserve the floor.

### Crowding

High ensemble density reduces competing density, especially in comping/melody
roles. Rhythm-section continuity is reduced less aggressively.

### Form boundary

Near a form boundary:
- drums may TRANSITION;
- bass tends to LOCK;
- other players continue to use their own form/harmony intelligence.

### No leader

If there is no clear leader, a designated soloist/melody/leader role may take
leadership. This prevents mutual-yield deadlock.

## Snapshot / causality rule

schedule_ensemble() computes all directives from one immutable EnsembleState
snapshot.

Players then evaluate and commit immediate actions. Only after commitments does
the app publish a new state generation and run the scheduler again.

This prevents ordering artifacts where the first player evaluated secretly sees
a different ensemble than the last player evaluated.

## Relationship to player branches

The scheduler says **what interaction role is useful**.

Player branches decide **how to realize it**:

- piano YIELD: sparser voicing, silence, shorter comp, reduced register claim;
- bass LOCK: stable pulse / harmonic orientation appropriate to current style;
- drums SETUP: style-specific setup gesture and orchestration;
- sax ANSWER: phrase response generated from sax grammar / memory.

Those examples belong in player policies, not Shared Core.

## Realtime target

v1.44 is the first scheduler contract needed for AI trio / quartet simulation.

Next runtime integration:

EnsembleState snapshot
-> InteractionScheduler
-> per-player candidate generation
-> Harmony + Interaction + Player evaluation
-> immediate commitments
-> RenderGesture projection
-> state update
-> repeat.
