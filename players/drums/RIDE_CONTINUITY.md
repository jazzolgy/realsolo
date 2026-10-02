# Bebop Ride Continuity Model

## Source-derived principle

The uploaded Riley material and Parker-compilation study support a distinction
between:

- **deep quarter-note forward motion**
- **surface ride vocabulary**

The familiar skip-beat is important vocabulary, but RealSolo should not reduce
bebop time to a repeated two-beat cell.

## Runtime representation

The current instant is classified as:

- `QUARTER`
- `SKIP`
- `OTHER`

At a quarter location the player may consider:

- HOLD_QUARTER
- ACCENT_QUARTER
- RELAX_SURFACE (exceptional quarter omission)
- REASSERT_TIME

At a skip location:

- LIFT_SKIP
- OMIT_SKIP
- ACCENT_SKIP

This is a candidate set for the **current instant only**.  No future ride
sequence is scheduled.

## Important asymmetry

Quarter omission and skip omission are deliberately different.

A skip note may be omitted rather freely because the deeper quarter-note pulse
can remain perceptually intact.

A quarter omission is more expensive.  It becomes safer when:
- the bass supplies a very strong shared pulse;
- the ensemble context supports a momentary surface relaxation.

Even then, repeated quarter omissions quickly create a `REASSERT_TIME`
candidate.

## Local ride memory

The drummer tracks only execution history:

- recent clear quarter hits
- recent quarter omissions
- recent skip hits
- recent skip omissions
- beats since a clear quarter
- last ride surface action

This is drummer-owned performance memory, not Shared Core semantic memory.

## Interaction

BUILD / HANDOFF can increase accent candidates.
COAST / COME_DOWN / LISTEN can increase skip omission.

The model therefore allows energy to change by altering the **surface** while
preserving the deeper time field.

## Bass coupling

A strong walking-bass projection can make a rare quarter omission less risky,
but does not turn quarter omission into the default.  The bass provides shared
pulse; the ride remains the drum-set's primary time identity.

## Next calibration

The numerical biases remain provisional.  They should be calibrated using
identified recordings and expert phrase-level annotations, especially:

- actual quarter-vs-skip hit rates
- consecutive skip omission lengths
- quarter accent placement
- ride behavior before/after horn phrase boundaries
- tempo dependence
- named-drummer differences
