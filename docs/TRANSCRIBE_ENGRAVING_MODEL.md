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
