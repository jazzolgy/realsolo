# Scorebook Linear Comparator — Current v1.54 Benchmark Results

## Purpose

Run the abstract scorebook observations from:

- Anthropology
- Autumn Leaves
- Actual Proof
- Asa (The Zoo Blues)

against the current Shared Scale/Linear v1.54 route generator.

This is not exact-note matching. The benchmark compares only route-family coverage and
evidence requirements.

## Result 1 — Anthropology exposes missing CHROMATIC_PASSING generation

Observed abstract route families from the score page:

- CHORDAL
- DIATONIC_PASSING
- CHROMATIC_PASSING
- APPROACH
- ENCLOSURE

Current Shared Core can generate, given current/future harmonic evidence:

- CHORDAL
- DIATONIC_PASSING
- NEIGHBOR
- APPROACH
- ENCLOSURE
- ANTICIPATION
- SCALE_FRAGMENT when the contextual field is sufficiently explicit
- ARPEGGIO_FRAGMENT
- COMMON_TONE when applicable

But current v1.54 code does **not** emit `CHROMATIC_PASSING`.

### Current benchmark interpretation

Route-family recall for the five high-confidence observed families is therefore at most:

`4 / 5 = 0.80`

before considering target/horizon weighting.

This is a real Shared Core gap identified by scorebook practice.

### Requested distinction

`CHROMATIC_PASSING` should not simply duplicate `NEIGHBOR` or `APPROACH`.

Potential semantic distinction:

- NEIGHBOR:
  - departs from and returns toward a local pitch identity;
- APPROACH:
  - aims directly at a known structural/future target;
- CHROMATIC_PASSING:
  - connects two distinct positions through non-field semitone/step motion;
  - may be target-directed but is not necessarily a final approach note.

The eventual implementation should remain one-event-at-a-time.

## Result 2 — Autumn Leaves has strong route-family coverage but needs ranking

High-confidence abstract observation:

- CHORDAL
- DIATONIC_PASSING
- APPROACH
- COMMON_TONE / sustained structural behavior

With current/future harmonic evidence and an explicit local field, v1.54 can expose all
of these families.

The main gap is therefore **not route existence**.

It is route ranking by:

- beats to harmonic change;
- phrase location;
- swing/section context;
- target arrival horizon.

Current v1.54 may expose many additional legal families at once:

- NEIGHBOR
- ENCLOSURE
- ANTICIPATION
- SCALE_FRAGMENT
- ARPEGGIO_FRAGMENT

This is musically acceptable as an affordance set, but the runtime needs better context
to avoid treating all legal routes as equally timely.

## Result 3 — Actual Proof validates conservative ScaleField behavior

The score contains pitch/color behavior compatible with scale/fragment thinking, but
also:

- NC;
- vamp-till-cue;
- mixed meter;
- written/sample keyboard material;
- section-specific cues.

When the Shared Core receives only chord-level evidence with fewer than five contextual
pitch classes, it intentionally does **not** emit `SCALE_FRAGMENT`.

This is correct behavior.

The lesson is:

> missing explicit field evidence should remain missing, not be repaired by a private
> Piano chord-scale table.

To recover scale-fragment affordances where musically justified, upstream evidence must
supply:

- local key / pitch field;
- explicit chord-color pitch classes;
- or verified score-derived harmonic material.

## Result 4 — Asa requires altered-color evidence upstream

The chart contains repeated altered-dominant notation and written rhythm-section
material.

The abstract line observation includes:

- CHORDAL
- SCALE_FRAGMENT
- CHROMATIC_PASSING
- ARPEGGIO_FRAGMENT

Current Shared Core can represent structural/arpeggio material when explicit chord pitch
classes are available, and scale fragments when a contextual field contains enough
verified pitch classes.

Again, the missing piece should **not** be a Piano-only altered-scale lookup.

Required upstream path:

```
scorebook chord/color evidence
-> HarmonicFrame / contextual ScaleField
-> Shared Linear route affordances
-> Piano realization
```

## Cross-benchmark diagnosis

### Strong current behavior

- evidence-driven ScaleField
- no invented scale from suffix
- shared approach/enclosure/anticipation semantics
- one-event commitment
- instrument-neutral pitch-class routes

### Missing or underdeveloped

1. actual CHROMATIC_PASSING generation;
2. target-arrival / harmonic-rhythm horizon;
3. route ranking by feel/section;
4. bounded enclosure route state;
5. verified score field evidence flowing into ScaleField;
6. common abstract comparator in Shared Core.

## Recommendation to Shared Linear/Scale Intelligence

Next highest-value Core changes:

1. implement CHROMATIC_PASSING as a distinct route;
2. add target-arrival horizon context;
3. preserve scorebook provenance/confidence into route affordances;
4. only then calibrate route weights from larger scorebook practice.

Do **not** add a chord-symbol-to-scale lookup as a shortcut.
