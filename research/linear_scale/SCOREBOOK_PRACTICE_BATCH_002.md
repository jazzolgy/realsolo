# Scorebook Practice Batch 002 — Canonical Ingestion Seeds

## Purpose

Second Shared Scale/Linear practice pass using only songs already registered by the
canonical Scorebook Ingestion Layer on main.

No complete melody is copied into this derived research record.

## Canonical seed sources reviewed

### Airegin — NewReal1 p.2

Score evidence visible on the page:

- Medium-Up Latin;
- head swings;
- ABAC solo form;
- solo break;
- piano tacets for head;
- explicit cue / coda navigation.

Linear/Scale implication:

A pitch route that is valid harmonically is not automatically valid as a Piano action.
Head-vs-solo role and piano tacet evidence must remain available to the player policy.

Shared Core should expose the evidence; Piano decides to lay out.

### Anthropology — NewReal1 p.11

Score evidence:

- Fast Bebop;
- rapid functional harmonic rhythm;
- repeated ii-V / dominant-target movement;
- melody contains dense stepwise and chromatic motion.

Derived linear lesson:

- short-horizon approach / passing / anticipation are first-class route families;
- route confidence needs time-to-target context;
- fast bebop should not be implemented as one memorized scale per chord;
- exact written melody is not stored in this practice result.

This page is a strong benchmark for future Parker Vocabulary × Shared Linear integration.

### Autumn Leaves — NewReal1 p.12

Score evidence:

- Medium Swing;
- repeated functional cycles;
- minor ii-V / dominant resolution;
- editorial note that melody is freely interpreted rhythmically.

Derived linear lesson:

- clear future harmony makes approach / anticipation testable;
- target selection and rhythmic realization should remain separate;
- the same harmonic route can be re-timed without changing its target meaning.

### Actual Proof — NewReal3 pp.1–2

Score evidence:

- Medium Funk;
- light piano comping in intro;
- vamp till cue;
- written/sample keyboard comping;
- explicit written bass page;
- NC passages;
- changing meters including 5/4, 4/4 and 3/4;
- solo on A; return/coda navigation.

Derived linear lesson:

1. NC must not silently produce a private chord-scale.
2. Meter and cue state affect route timing even when pitch affordances are unchanged.
3. Written-part evidence can override or constrain free candidate generation.
4. Vamps need recurrence-aware linear behavior rather than endless novel scale motion.
5. A full Shared Linear request will eventually need:
   - harmonic evidence;
   - meter/time position;
   - section/cue state;
   - target horizon;
   without collapsing these into one scale label.

### Asa (The Zoo Blues) — NewReal2 pp.9–10

Score evidence:

- Medium Funk;
- altered dominant colors;
- dedicated written bass page;
- solo on ABC;
- repeated functional/motivic regions.

Derived linear lesson:

- altered dominant pitch availability must come from explicit harmonic evidence, not
  from a hard-coded Piano scale lookup;
- written line comparator should analyze abstract properties:
  - structural target relation;
  - chromatic approach;
  - scalar motion;
  - interval/motion class;
  - register trajectory;
  - rhythmic density;
  rather than exact note copying.

## Shared Scale/Linear conclusions after Batch 002

### Confirmed

1. Evidence-driven ScaleField remains correct.
2. Immediate route semantics are reusable across swing, bebop, funk, Latin and ballad.
3. Player-specific realization must remain downstream.
4. Scorebook evidence must stay orthogonal to scale identity.

### New high-priority context requirements

#### A. Target arrival horizon

Need an instrument-neutral concept such as:

```
beats_to_target
beats_to_harmonic_change
target_arrival_confidence
```

Reason:
an approach one eighth-note before a dominant target is not the same musical action as
the same pitch class two bars earlier.

#### B. Meter-aware route timing

Actual Proof demonstrates that changing meter is score evidence, not a player detail.

Linear route semantics can remain beat-relative, but runtime needs reliable meter /
position context from Shared Form/Time intelligence.

#### C. Written-part gate

A score may contain:
- written piano figure;
- dedicated written bass part;
- tacet;
- explicit fill;
- vamp-until-cue.

Before free linear generation, a player should know whether a written/required part
currently occupies the action.

This is a score-evidence / player-policy gate, not a ScaleField rule.

#### D. Recurrence / vamp context

A vamp should permit:
- pattern continuity;
- controlled variation;
- common-tone retention;
- selective color;

without forcing constant route novelty.

Shared Linear should be able to receive recurrence/context tags from Shared Form /
Harmony memory.

## Piano implementation status

The Piano branch now consumes v1.54 route affordances via:

`players/piano/shared_linear_adapter.py`

and the bebop runtime can request Shared Linear routes when a HarmonicFrame is present.

Compatibility fallback remains for older callers that do not yet provide Shared Linear
affordances.

## Next practice target

The next batch should compare:

1. Fast bebop — Anthropology;
2. functional medium swing — Autumn Leaves;
3. medium funk / irregular meter — Actual Proof;
4. altered funk / written line — Asa;

using a common abstract route comparator.

Comparator output should include:

- observed route family;
- structural target class;
- interval-motion class;
- chromatic vs field motion;
- contour;
- harmonic boundary timing;
- phrase/section role;
- confidence/provenance.

No complete score melody should be stored.
