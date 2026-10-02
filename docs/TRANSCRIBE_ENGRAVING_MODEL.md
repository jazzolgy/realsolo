# Transcribe Engraving Model

## Purpose

The transcription system must separate **what the score means** from **how the
score is engraved**.

This is consistent with the architecture already used by professional notation
software such as Sibelius, where musical objects and engraving rules are
separate concerns.

## Core separation

```
Performance Evidence
-> Musical Structure
-> NotationIntent
-> NotationCandidate
-> LogicalScore
-> EngravingIntent / EngravingPlan
-> Optical Layout
-> MusicXML / renderer adapter
```

### LogicalScore owns

- written score-time onset / duration
- pitch spelling
- rests
- ties
- tuplets as rhythmic semantics
- articulation / musical markings
- logical voice identity
- logical staff identity
- source evidence / provenance

### EngravingIntent owns

- stem direction
- beam grouping / beam state
- cross-staff visual target
- tie visual placement
- tuplet bracket / placement preference
- spacing weight
- collision priority
- bar-rest hiding associated with cross-staff engraving
- renderer-neutral visual policy

### Optical Layout owns

- local collision pressure
- accidental clearance
- articulation / marking clearance
- simultaneous-voice collision pressure
- cross-staff clearance
- renderer-neutral spacing adjustment

None of these layers may rewrite the original performance evidence.

## Sibelius-informed design observations

The following observations are used as architecture guidance, not as a goal to
clone Sibelius's file format or UI.

### Engraving rules are independent policy

Sibelius exposes score-wide engraving rules for many categories rather than
baking visual geometry directly into note identity.

Our equivalent is `EngravingProfile`.

### Cross-staff notation is not one operation

Recent Sibelius releases separately improved:

- cross-staff beaming
- cross-staff bar rests
- cross-staff accidentals
- cross-staff ties
- cross-staff voice-positioning rules

This reinforces the rule that "cross-staff" is not merely a changed staff ID.
The musical voice remains stable while multiple visual subsystems respond.

### Voice identity and stem placement are separate

The logical voice is decided before engraving.

When independent voices coincide on one staff, the engraving layer may use
opposing stem directions to make the voices readable. Changing stem direction
must not change `voice_id`.

### Beaming follows meter / score-time grouping

Beaming is based on written rhythmic grouping rather than performed
microtiming.

The initial implementation uses:

- simple meter: written beat unit
- 6/8, 9/8, 12/8: dotted-beat groups

Further grouping rules can later use style / phrase / notation context.

### Optical spacing is not rhythmic duration

Accidentals, multiple voices, articulations, tuplets and cross-staff notation
can require more horizontal or vertical clearance while note duration remains
unchanged.

The `layout.py` pressure model therefore never alters `ScoreSpan`.

## Current modules

- `score.py`: logical score semantics
- `engraving.py`: engraving profile and per-event visual intent
- `layout.py`: renderer-neutral optical spacing / collision pressure
- `musicxml.py`: output projection; optionally consumes an EngravingPlan

## Non-goals

The current implementation does not yet attempt to reproduce Sibelius's exact
geometry, fonts, spacing tables, or proprietary engraving algorithms.

The goal is to develop a musical/notation intelligence layer that can later
drive Sibelius, Dorico, MuseScore, MusicXML or another renderer without making
any one renderer the source of musical truth.


## Sibelius defaults currently mirrored

The following behaviors are based on Avid reference/release documentation and
are treated as renderer-informed defaults rather than universal notation law:

- In 2/4, 4/4 and 2/2, consecutive eighth notes may beam in groups of four.
- 6/8, 9/8 and 12/8 use dotted-beat grouping.
- Beam groups may break when the written rhythmic pattern changes.
- Tuplets are, by default, positioned by considering the tuplet as though all
  notes were beamed together rather than using only the first note.
- A profile option can separate tuplets from adjacent beamed notes.
- Cross-staff ties can reuse ordinary tie-position rules.
- Cross-staff voice-position rules, accidental spacing, ties and beams remain
  separate engraving concerns.

## Current approximation boundaries

The following are still simplified and must not be mistaken for exact Sibelius
algorithms:

- tuplet above/below placement currently uses a renderer-neutral pitch/register
  proxy rather than Sibelius's exact staff/beam geometry;
- tie curvature and exact optical anchor points are not yet modeled;
- primary/secondary beam geometry is not yet represented;
- cross-staff beam slope and stem endpoint geometry are not yet represented;
- notehead displacement for seconds/unisons in multi-voice writing is not yet
  implemented;
- grace-note spacing and accidental column packing are not yet implemented.

These items are next-stage engraving intelligence tasks.


## Advanced layout / beaming implemented

- primary and secondary beam levels are represented separately;
- simple-meter secondary beams subgroup at quarter-note units;
- compound-meter secondary beams subgroup at dotted-quarter units;
- cross-staff beam-corner avoidance is modeled as a primary-beam-side policy;
- simultaneous independent voices at unison/second can request opposite
  notehead displacement sides;
- simultaneous accidentals are packed into renderer-neutral columns;
- grace-note identity is logical notation, while grace spacing remains a
  separate layout decision;
- MusicXML projection can emit level-1/level-2 beams and grace-note elements.

These remain semantic/engraving decisions rather than exact glyph geometry.
