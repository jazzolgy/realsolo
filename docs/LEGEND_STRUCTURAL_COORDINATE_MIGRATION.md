# Legend Structural Coordinate Migration

This policy applies to every current and future performer/Legend research tree.

## Canonical rule

Absolute audio time is provenance only.

The canonical learning coordinate is musical structure:

song
→ arrangement segment
→ core form
→ section
→ section bar
→ form bar
→ beat
→ subdivision
→ chorus/recurrence
→ phrase/harmonic/cadence position
→ role / motif state / ensemble state

Raw timestamps are preserved so the source can always be revisited.

## Migration rule

Existing observations are not discarded. They are classified as:

- `STRUCTURE_ALIGNED`: usable for musical comparison
- `FORM_ALIGNED`: form length/bar known, exact score bar may be absent
- `SECTION_ALIGNED`: section known, finer bar mapping pending
- `NAVIGATION_ONLY`: timestamp/feature only; not eligible for musical policy
- `PENDING_ALIGNMENT`: source identity verified but musical position not yet mapped

No timestamp-only observation may be promoted directly into Legend tendency,
vocabulary, or runtime policy.

## Arrangement exceptions

Rubato intros, written intros, pickups, interludes, vamps, tags, cadenzas,
metric/feel transitions, codas and outros are first-class arrangement segments.

They must not be forced into the recurring core-form grid unless the return/map
relationship is verified.

## Cross-instrument rule

The same structural coordinate is consumed by Piano, Bass, Drums, Sax and future
players. Instrument-specific interpretation comes after structural alignment.
