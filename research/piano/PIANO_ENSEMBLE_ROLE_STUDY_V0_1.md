# Jazz Piano Ensemble Role Study v0.1

## Trigger

Review of the uploaded reference render:

`RealSolo_Along_Came_Betty_Trio(1).wav`

Duration: ~59.88 s.

Primary qualitative issue heard in the render:

- piano comping attacks recur with too much rhythmic regularity;
- piano remains too strongly in accompaniment mode for a piano-bass-drums trio;
- when piano is the only melodic/harmonic foreground instrument, the texture lacks a
  sufficiently independent right-hand melody/solo role.

This study separates **ensemble role** from **comping technique**.

## Source-derived ensemble principles

### McNeely — comping as interaction

Useful listening questions include:

- where chords are placed rhythmically;
- long vs short durations;
- active vs sparse accompaniment;
- imitation / call-and-response with the soloist;
- how much space is left;
- interaction with drummer accents and turnarounds;
- interaction with bassist substitutions and register;
- changes of voicing weight, density and color.

Design conclusion:
comping rhythm should not be a repeating accompaniment pattern unless the musical
context explicitly supports a pattern/vamp.

### Jazzology / standard rhythm-section practice

Comping is both chordal and rhythmic.

Important behaviors:

- rhythmic variety;
- alternate voicings;
- space;
- velocity/dynamic balance;
- sustained sonority when appropriate;
- awareness of the rest of the rhythm section.

Design conclusion:
a change of chord symbol is not itself an instruction to attack a chord.

### Hal Galper — pianist as colorist

When bass and drums already provide roots/time, piano is not required to duplicate
those functions continuously.

The pianist can behave as:

- harmonic colorist;
- rhythmic colorist;
- melodic respondent.

Design conclusion:
"When?" is as important as "what?". Piano comping should react to foreground phrases
rather than independently emit a regular metronomic layer.

### Piano-trio interaction

In interactive piano trios, bass and drums are not merely backing instruments. The
three musicians may operate conversationally.

Design conclusion:
the piano must know whether it currently owns the foreground or is supporting another
foreground player.

## RealSolo piano ensemble modes

### 1. External melody / horn solo support

Typical role:

```
RH + LH:
  two-hand comping / voicing / response / color
foreground:
  external melody instrument
```

Possible piano behaviors:

- two-hand rootless/spread voicings;
- counter-lines;
- fills after phrases;
- lay out;
- punctuation with drums;
- harmonic color.

The piano should not shadow every melody event.

### 2. Piano-led trio — head

When piano is the only melody-capable foreground instrument:

```
RH = melody / head interpretation
LH = comping / harmonic support / space
bass = bass function + interactive countervoice
drums = groove + interaction
```

LH does not need to play every chord.

Valid LH behaviors:

- shell / guide-tone support;
- brief rootless color;
- anticipation;
- offbeat punctuation;
- sustain;
- lay out;
- bass/drum response.

Two-hand block/head textures may appear intentionally, but are not the default state.

### 3. Piano-led trio — piano solo

Default contract:

```
RH = improvised foreground solo
LH = comping
```

The two hands are one musician, not two independent agents.

LH must listen to:

- current RH activity;
- RH register;
- RH phrase ending;
- RH harmonic coverage;
- bass register/activity;
- drummer activity;
- current ensemble density.

If RH is dense:
- LH may lay out;
- play one shell/punctuation;
- use lower density;
- avoid duplicating RH register.

If RH leaves space:
- LH may answer;
- increase harmonic identity;
- punctuate;
- alter rhythm/voicing;
- sometimes remain silent.

### 4. Bass solo

Foreground ownership moves to bass.

Piano may:

- sparse two-hand or LH support;
- conversational RH response;
- simplify low register to avoid masking bass;
- lay out;
- mark form/cadence boundaries.

### 5. Drum solo / drum feature

Piano may:

- lay out;
- provide form cues;
- trade punctuation;
- use sparse rhythmic hits;
- answer drummer figures.

Continuous harmony is usually not an obligation.

### 6. Collective trio interplay

Roles can shift moment by moment.

Foreground ownership can become plural or ambiguous.

The piano needs an interaction model rather than a fixed hand pattern.

## Comping rhythm diagnosis

Previous RealSolo grammar exposed:

- ON_BEAT for every sounding candidate;
- anticipation/offbeat mainly for PUNCTUATE/ANCHOR;
- delayed placement mainly for ANSWER/FILL.

Therefore ordinary SUPPORT candidates had effectively one preferred timing vocabulary.

This structurally encouraged regular comping.

## Corrected immediate rhythm vocabulary

General support now has plural immediate possibilities such as:

- short on-beat;
- long on-beat;
- eighth-note anticipation;
- small anticipation;
- offbeat eighth;
- smaller delayed/offbeat displacement;
- delayed quarter-like placement;
- sustained gesture when justified.

These remain **one current gesture only**.

RealSolo still does not schedule a future two-bar comping pattern.

## Rhythmic memory

The player now tracks a more specific `rhythm_cell`.

Repeated cells receive variation pressure even when voicings change.

A short periodic A-B-A-B loop can also be penalized unless real pattern/vamp evidence
justifies continuity.

Therefore:

```
same harmony progression
!=
same comping rhythm
```

and:

```
variation
!=
random rhythm
```

The target remains context-aware conversational timing.

## New piano-trio hand contract

Current experimental canonical rules:

### PIANO_HEAD_TRIO

- RH: MELODY
- LH: COMPING
- Piano owns foreground.

### PIANO_SOLO_TRIO

- RH: IMPROVISED_SOLO
- LH: COMPING
- Piano owns foreground.

When either mode is active:

- LH-only comping realizations are generated;
- RH-occupied comping is penalized;
- compact LH realizations are rewarded;
- LH listens to RH foreground activity/register.

### EXTERNAL_MELODY_SUPPORT

- two-hand comping remains available;
- Piano does not own foreground by default.

## Important nuance

"RH solo + LH comping" is a default role contract, not a permanent mechanical texture.

Expert piano trio playing may intentionally use:

- no LH comping for a stretch;
- single-line RH alone;
- two-hand octaves;
- block chords;
- two-hand line;
- RH chordal punctuations;
- counterpoint;
- register swaps.

The role model must therefore constrain **ownership and collision**, not forbid creative
texture changes.

## Next evaluation

Re-render Along Came Betty with:

1. piano as sole melodic instrument;
2. head: RH melody + LH context-aware comping;
3. solo: RH bebop solo + LH comping;
4. LH rhythm-cell repetition penalty enabled;
5. LH listening to RH activity/register;
6. two-hand comping allowed only in explicit texture-change episodes.

Compare against the uploaded render for:

- foreground continuity;
- comping rhythmic predictability;
- silence distribution;
- RH/LH register collisions;
- phrase-level interaction;
- bass/drum conversational response.
