# Scorebook Practice Batch 001 — Shared Scale/Linear Feedback

## Scope

First cross-book practice pass over the nine uploaded Real/New Real/Vocal/Christmas
collections.

This pass does **not** store or reproduce copyrighted melodies. It records only
abstract score evidence and Shared Scale/Linear behavior.

## Seed pages

| Book | Page(s) | Seed tune / section | Abstract evidence |
| --- | ---: | --- | --- |
| RealBk3 | 6 | Alanjuneally | even-8th context, dense harmonic motion, altered/half-diminished colors |
| RealChBk | 7 | Almost Day | bright functional/diatonic baseline outside bebop context |
| VcRealBk1 | 7–8 | A Night in Tunisia | Afro feel, interlude, solo break, changing section roles |
| VcRealBk2 | 7–8 | Like Someone in Love | standard functional ballad/swing vocabulary |
| NewReal1 | 7–8 | Ana Maria | half-time rock, bossa, rock-feel changes inside one form |
| NewReal2 | 7–8 | Along Came Betty | medium swing, dense functional movement, explicit solo/role evidence |
| NewReal3 | 5–8 | Ain't That Peculiar | medium rock, repeated rhythmic/harmonic pattern, explicit rhythm section writing |
| RealBk1 | 7 | A Night in Tunisia | medium Afro, interlude / solo-break structure |
| RealBk2 | 4 | Alfie's Theme | explicit two-feel -> in-four -> back-to-two change |

## What v1.54 already gets right

### 1. Evidence-driven ScaleField

Keep the rule:

> no explicit local-key evidence -> do not invent a compulsory seven-note scale from
> the chord symbol alone.

The seed charts contain:
- dense harmonic rhythm;
- sus/altered colors;
- slash/upper-structure-like symbols;
- section-specific harmonic treatments;
- feel changes that do not imply a different chord-scale dictionary.

A private chord-suffix -> scale table in Piano would be especially harmful here.

### 2. Immediate route semantics

The existing shared route vocabulary is musically useful across the seed:

- chordal
- diatonic passing
- chromatic passing / neighbor
- enclosure
- scale fragment
- arpeggio fragment
- common tone
- approach
- anticipation

These should remain instrument-neutral.

### 3. One-event runtime contract

The scorebook pass does not justify precomposing full lines.

A chart can support an intention such as:
- approach next harmony;
- retain common tone;
- continue diatonically;
- build an enclosure intention;
- anticipate a target;

while the actual next event remains re-evaluated at runtime.

## Gaps exposed by the scorebooks

### G1 — Feel / section context should modulate route weighting

Observed score evidence includes explicit changes such as:

- two feel -> in four -> back to two;
- half-time rock -> bossa -> rock;
- vamp until cue;
- interlude;
- solo break;
- head vs solo role.

The set of legal pitch classes may stay the same while the **musical plausibility of a
route** changes.

Example design implication:

- a scale fragment that is plausible in an open Bossa section may be too busy in a
  sparse two-feel phrase;
- chromatic approach density appropriate to medium swing may be inappropriate in a
  sustained straight-8th ballad;
- an anticipation route around a solo break should be evaluated differently from the
  same route inside uninterrupted head melody.

Recommendation:
Shared Core should receive or reference structured ingestion evidence such as
`feel_change`, `section_role`, and form boundary state. Core need not prescribe a
Piano action, but route affordances should expose contextual tags / weighting hooks.

### G2 — Harmonic-rhythm / time-to-change should be explicit

The same approach/enclosure family behaves differently when:

- harmony lasts several bars;
- harmony changes every bar;
- harmony changes twice within a bar;
- a target is only a fraction of a beat away.

Recommendation:
add a shared notion such as:

```
beats_to_harmonic_change
harmonic_rhythm_density
target_arrival_horizon
```

to linear-route context.

This should influence route **availability/confidence**, not schedule exact notes.

### G3 — Enclosure requires bounded multi-tick state

v1.54 correctly marks enclosure as a multi-event intention, but the current first-step
implementation exposes the same immediate chromatic neighbors as a generic approach.

That is acceptable for v0.1 but insufficient for learning real enclosure behavior.

Needed shared state is abstract:

```
active_route = ENCLOSURE
target_pc
sides_remaining / route_stage
resolution_debt
started_at
confidence
```

It must not contain a frozen future pitch sequence.

### G4 — Section role must remain separate from scale identity

Scorebook evidence repeatedly distinguishes:
- head;
- solo;
- interlude;
- vamp;
- solo break;
- cue-based transition.

These are not scales.

They should affect:
- route density;
- anticipation permission;
- phrase continuation;
- space;
- candidate family weighting;

without redefining the harmonic field.

### G5 — Provenance/confidence should survive into linear evidence

When the future ingestion layer reads a scan page, route reasoning should retain:

- book / source id;
- page span;
- score evidence confidence;
- harmonic evidence provenance;
- style/feel evidence provenance.

A low-confidence parsed chord or section instruction must not become a high-confidence
linear rule.

## Piano implementation consequence

Piano now consumes Shared Scale/Linear affordances through:

`players/piano/shared_linear_adapter.py`

Shared Core owns:
- route semantics;
- immediate pitch-class affordances;
- target pitch classes;
- tension/resolution meaning.

Piano owns:
- MIDI register realization;
- right-hand range;
- local physical feasibility;
- touch/articulation;
- interaction with left-hand comping.

When shared affordances are supplied, Piano no longer independently generates its own
approach/neighbor/passing semantics. The old local connector path remains only as a
compatibility fallback.

## Next practice batches

1. functional fast swing / bebop;
2. static/modal fields;
3. ballads and straight-8th writing;
4. Latin/Bossa/Afro sections;
5. funk / repeated-vamp material;
6. tunes with explicit feel changes;
7. tunes with written rhythm-section parts;
8. written line vs Shared Linear route comparator using abstract features only.

## Copyright / memory boundary

Practice results store:
- route family;
- target relation;
- interval/function statistics;
- contour category;
- harmonic-rhythm context;
- feel/section context;
- confidence/provenance.

They do not store the complete copyrighted melody as a generated training asset.
