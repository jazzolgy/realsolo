# Cross-Source Piano Comping Study v0.2

Sources in this pass:

- Jim McNeely, *The Art of Comping*
- Dan Haerle, *Jazz Piano Voicing Skills*
- Per Danielsson, *Piano/Guitar Comping — How to Avoid Conflicts*
- Bill Dobbins, *A Creative Approach to Jazz Piano Harmony*
- Haerle/Levine, *Jazz Piano Voicings — Freddie Hubbard* transcription volume
- *Piano Voicing Overview* extract
- Ted Pease, classic jazz sextet arranging article

## 1. What is now cross-source supported

### 1.1 Listening and role awareness are not optional

McNeely emphasizes interaction with soloist, drums, and bass.

Danielsson independently emphasizes:

- role awareness in a small group;
- listening and on-the-spot judgment;
- avoiding conflict between piano and guitar when both can comp, solo, provide rhythm,
  and play melodic material;
- support of the soloist as the primary reason for comping.

This upgrades interaction role and role occupancy from a McNeely-only design
inference toward cross-source support.

### 1.2 Silence / reduced activity is a legitimate ensemble solution

McNeely repeatedly asks the pianist to leave space.

Danielsson gives a more explicit multi-comping-instrument case:

- switch off between piano and guitar;
- when guitar continuously supplies harmony, piano may play sparsely and rhythmically;
- do not add material merely because both players have the same written part.

Therefore RealSolo should model silence not only as response to a busy soloist, but also
as response to functional coverage by another accompanist.

### 1.3 Voice-leading is a strong prior, not the entire objective

Haerle repeatedly describes smooth connection through:

- common tones;
- step-wise motion;
- horizontal motion of individual voices;
- 3rd/7th-based inversions.

This validates a strong voice-leading prior.

However, Dobbins explicitly argues for broad harmonic possibility, listening to the
individual lines inside voicings, and avoiding a narrow stock-voicing mentality.

Therefore minimum motion should remain a default continuity prior, not a universal optimum.
Color, melodic-line intent, register, texture, and interaction may justify larger movement.

### 1.4 Voicing-family plurality is well supported

Haerle provides independent support for a substantial family taxonomy including shell
voicings, modal fourth-based voicings, So What voicings, fourth-based II-V-I, tritone
substitution II-V-I, polychordal II-V-I, altered-dominant cycles, polychordal blues,
fourth-based blues, dominant seventh polychords, and diminished substitutions.

This supports RealSolo's plural-candidate architecture and argues against a single
chord-symbol-to-voicing lookup.

### 1.5 Upper structures / polychords should preserve horizontal voice logic

Haerle repeatedly couples upper structures with instructions to notice horizontal
motion and smooth connection. Therefore upper-structure generation should not be
implemented as a purely vertical formula table. Candidate evaluation must retain
voice identity / voice-leading.

### 1.6 Bass presence changes harmonic responsibility

The Piano Voicing Overview explicitly presents basic left-hand voicings for use with a
bass player and frees the right hand for single notes, octaves, triadic shapes, upper
extensions, or single-line solo material.

Ted Pease's arranging article independently notes that bass often covers root/fifth,
allowing upper voices to prioritize guide tones and tensions.

This supports a generic bass coverage concept rather than a fixed rule that piano
must include roots.

### 1.7 Accompaniment should be supportive without eliminating creativity

Dobbins treats accompaniment as fully creative musical activity while warning against
dictatorial/oppressive accompaniment and emphasizing the scarcity/value of good
accompanists.

This is compatible with RealSolo's design: rich candidate generation plus restrained
policy when soloist/ensemble context calls for it.

## 2. New distinction: ensemble density vs functional coverage

ensemble_density alone is insufficient.

Example:

- Scenario A: high drum/bass/solo activity, no chordal accompanist.
- Scenario B: same overall density, but guitar already provides continuous harmony.

Piano behavior may differ substantially.

Add separate estimates:

- other comping activity
- other harmonic coverage
- other rhythmic coverage
- comping priority / role occupancy
- harmonic-agreement confidence

This is implemented provisionally in players/piano/role_occupancy.py and proposed to
Core as CR-004.

## 3. Current source-status changes

### Promoted toward CROSS-SOURCE-CONFIRMED

- listening / role awareness
- support of soloist
- silence / lay-out as meaningful action
- sparse response under competing accompaniment
- smooth voice-leading as a major default objective
- plurality of voicing structures
- register / role sensitivity to bass presence
- variation inside stable harmonic context

### Still DESIGN-INFERENCE

- exact RealSolo role enum names
- OPEN_DIALOGUE / SOLOIST_LEAD / DENSITY_SHIFT episode labels
- numerical score weights
- exact thresholds for phrase-space, density, and role occupancy
- current mapping from voicing families to BUILD/ANCHOR/SUPPORT
- current decay rules for episode memory

## 4. Important contradiction / nuance to preserve

The sources do not support a simple rule: avoid repetition.

Danielsson values clear, consistent comping patterns so another accompanist can play
around them. McNeely also demonstrates recurring rhythmic identities.

Therefore RealSolo should continue distinguishing exact mechanical repetition,
pattern/groove continuity, motif continuity, and expressive/registral/voicing variation.

## 5. Freddie Hubbard transcription volume

This source is especially valuable because it is not merely a rule book: it contains
transcribed comping by Dan Haerle and Mark Levine over repertoire associated with the
Freddie Hubbard play-along.

It should be treated as observational performance evidence, not a universal grammar.

Next extraction should annotate selected choruses for onset density, silence spans,
repeated rhythmic cells, voicing-size changes, register center and span, parallel/chromatic
inner motion, sustained vs punctuating gestures, phrase-boundary behavior, and repeated
harmonic situations with different realizations.

The transcriptions should not be converted into memorized literal phrase templates.

## 6. Architecture implication

Updated immediate-decision context:

```
harmony / form
  + soloist state
  + drummer state
  + bass state
  + ensemble density
  + accompaniment role occupancy
  + harmonic/rhythmic coverage
  + recent gesture memory
  + response / episode memory
        ↓
candidate role
        ↓
voicing family
        ↓
rhythmic placement
        ↓
register / dynamics / touch
        ↓
variation / continuity
        ↓
one immediate gesture
```

## 7. Style presets remain intentionally uncommitted

The new sources do provide evidence of style-dependent textures and voicing systems,
but they do not justify freezing a user-facing Old / Modern / New taxonomy yet.

For now collect dimensions, not labels:

- functional vs modal/non-functional
- tertian vs fourth-based vs polychordal
- compact vs open register
- sparse vs dense
- pattern-consistent vs highly variable
- explicit harmony vs color/ambiguity
- primary-support vs highly reciprocal interaction