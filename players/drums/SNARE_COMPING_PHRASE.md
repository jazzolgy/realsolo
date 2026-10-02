# Bebop Snare Comping Phrase Memory

## Source basis

The uploaded John Riley bop method treats comping as accompaniment rather than
technical display.  Its pacing and rhythmic-transposition material supports
three important design decisions:

1. a comping idea can be stated and then left alone;
2. recognizable material can return after space;
3. rhythmic identity can be moved to another phrase position rather than copied
   only at the original location.

This module encodes those principles.  It does **not** claim that the current
numerical weights are transcribed probabilities from Riley or from the Parker
compilation.

## Why this is separate from generic comping density

A subdivision-independent probability model tends to produce:
- too many unrelated snare events;
- immediate replies to every soloist event;
- no audible memory;
- no distinction between repetition and return.

The phrase engine instead tracks local execution history:

- compact snare motif identity
- bars since motif statement
- consecutive related statements
- bars since any snare statement
- last statement phase
- recent space

## Current phrase-development actions

- STATE
- REPEAT
- RETURN
- DISPLACED_RETURN
- VARIATION
- PUNCTUATE
- LEAVE_SPACE

Immediate repetition is intentionally weaker than a recognizable return after
space.  This is the first implementation of **pacing**.

## Motif identity

A local motif is currently represented by normalized onset phases and optional
accent phases.  This is intentionally compact.

The runtime still commits one event at a time.  A multi-onset motif can be
assembled retrospectively from already committed events, but it is never used
to freeze future snare hits.

## Rhythmic transposition

A displaced return uses the same local identity shifted to another phase in the
bar.  This is a drummer-owned realization of source-supported rhythmic
transposition; it is not Shared Core motif semantics.

## Interaction

COAST / LISTEN / COME_DOWN raise LEAVE_SPACE.
BUILD can favor displaced/active returns.
HANDOFF / late phrase position can favor PUNCTUATE.

The target is a drummer whose comping has **memory and pacing**, not a random
syncopation generator.
