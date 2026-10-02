# AI Bassist v1.46 — Bebop Interaction Grammar and Performance Memory

## Why this slice exists

The previous bass slices improved pitch choice, contour and stepwise motion, but
a bebop bassist is not adequately modeled as a chord-to-note generator.

The uploaded Charlie Parker-era listening study highlighted a more important
behavioral distinction:

- shared pulse does not imply identical accent streams;
- soloist phrase endings create response opportunities, not fill obligations;
- stable time/harmonic floor can be the musically responsive choice;
- stepwise motion is useful but should not continue indefinitely;
- register excursions need recovery;
- recent bass complexity should influence what the bass does next.

v1.46 therefore adds two bass-local layers while leaving Shared Core ownership
unchanged.

## Shared Core boundary

Shared Core remains authoritative for:

- EnsembleState
- InteractionScheduler
- form / transport
- harmony / future harmony
- generic phrase and leadership state
- instrument-neutral interaction kinds

Bass consumes that state and answers:

> How should a bassist realize this coordination role right now?

## BassPerformanceMemory

The bass now stores only already-committed actions.

It derives a compact snapshot:

- recent pitches / intervals
- consecutive step count
- consecutive direction count
- phrase register center
- phrase register slope
- recent accent mean
- recent density
- ghost/dead-note count
- recent local complexity

This is causal memory. It never stores a precomposed future line.

## Bass interaction vocabulary

Bass-specific intention:

- ANCHOR
- PROPEL
- CONNECT
- YIELD
- ANSWER
- FILL
- BUILD
- RELEASE
- RESET
- HOLD

These are realizations of Shared Core interaction semantics, not replacements for
the Core vocabulary.

## Response opportunity policy

A soloist phrase ending does not mean "bass fill now".

The system accumulates a response opportunity. It may become ANSWER only if:

- ensemble context leaves space;
- drums/piano are not already filling;
- recent bass complexity is low enough.

If another rhythm-section voice is already filling the opening, bass yields.

## Complexity debt

If the bass has recently been too active, v1.46 can produce HOLD.

This is deliberate. Musical responsiveness may mean preserving the floor rather
than producing another novel gesture.

## Stepwise and contour memory

Three or more consecutive stepwise moves create saturation pressure.

Three or more moves in the same direction create recovery pressure.

The immediate realizer then softly:

- penalizes another same-direction continuation;
- rewards contrary recovery;
- may reduce directed/chromatic activity under HOLD/YIELD/RESET;
- may favor directed connection under CONNECT/PROPEL/ANSWER/BUILD.

No exact future note is stored.

## Register recovery

A sustained positive register slope creates downward-recovery preference; a
negative slope creates upward-recovery preference.

This is not a hard range clamp. High-register excursions remain possible, but
the system now has memory that they occurred.

## Next slice

The next important performance dimensions are:

1. performed note length separate from notated duration;
2. accent intent separate from harmonic importance;
3. microtiming relative to a shared pulse, not a fixed global delay;
4. sparse ghost/dead-note articulation as an interaction/groove event;
5. live coupling to drums, piano and soloist evidence.

These should be evaluated in the same immediate-commit / listen-again loop.
