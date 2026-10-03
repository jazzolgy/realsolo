# Bill Evans — Form-Relative Expressive Realization Study v0.1

## Question

This study asks **HOW an already selected phrase is performed**, rather than
which notes are chosen.

The target variables are:

- phrase dynamic shape
- accent grammar
- note body / sustain
- timing emphasis
- register / brightness relation
- foreground/background weight
- repetition variation
- cadential release
- climax construction

The canonical coordinate is musical position:
form / section / bar / beat / chorus / performance phase.
Elapsed seconds are provenance only.

## Evidence used

1. Existing Bill Evans 100-pass and 1000-pass studies.
2. Existing 24-track form map and form-relative restudy.
3. Existing score/form alignment for Autumn Leaves.
4. A new targeted analysis of the owner-supplied Autumn Leaves recording:
   - head: A1/A2/B/C
   - first piano-solo chorus: A1/A2/B/C
   - each 8-bar section divided into form bars
   - harmonic-component RMS / centroid and mixed-audio onset strength.

Important limitation: this is mixed audio. HPSS harmonic energy is **not isolated
Bill Evans piano**. Therefore the numeric evidence below is ensemble/harmonic
proxy evidence until source separation or manual note-level attribution confirms
the pianist.

## Cross-track evidence already in the dataset

The existing corpus already rejects several simple expression rules.

### Sparse does not mean expressively flat

Blue In Green shows a large macro-dynamic arc despite relatively low attack
density. My Foolish Heart combines low attack density with high accent
variability.

Therefore:

`density != dynamic information`

and

`number of attacks != expressive intensity`.

A Shared expression layer needs note body, decay/release, accent and silence as
first-class variables.

### Development does not imply one universal crescendo

Autumn Leaves has strong internal change while the harmonic roadmap repeats.
Nardis and other tracks contain expansion and contraction rather than one
monotonic rise.

Therefore the learnable relation is:

`development type × form position × performance phase × ensemble state
-> expression trajectory`

not:

`development -> louder`.

### Accent is relational

The 1000-pass study already concluded that accent meaning depends on piano
density, drum setup/fill, phrase maturity, harmonic arrival and preceding note
body. This argues against a fixed beat-strength table as the primary accent
grammar.

## Autumn Leaves: same form, different expressive realization

The new form-relative proxy analysis provides a useful controlled comparison:
the same 32-bar form appears in the head and in a piano-solo chorus.

### 1. Performance phase changes absolute expressive level

Across matched form bars, the solo harmonic-component level is higher than the
head in 22 of 32 bars, lower in 10 of 32 bars, with mean difference about
+1.66 dB.

This is not a rule that solo must be louder. It is evidence that **the same form
address does not have one fixed dynamic realization**.

The learning key should therefore include at least:

`form position × performance phase × current ensemble role`.

### 2. Dynamic energy and accent strength separate

Head C has the strongest mean harmonic-component level among head sections
(-21.26 dB) while its mean attack-strength proxy is the weakest head value
(1.595).

The solo shows the same type of separation: solo C has the strongest mean
harmonic level (-20.86 dB), but the strongest attack proxy occurs in solo A2,
not C.

This is direct architectural evidence for keeping these separate:

- perceptual_intensity
- dynamic_level
- accent_strength
- note_body

A single MIDI velocity variable cannot represent the observed relationship.

### 3. Expression has phrase/section shape

Within-section dynamic ranges are substantial:

- Head A1: ~6.2 dB
- Head A2: ~6.7 dB
- Head B: ~8.9 dB
- Head C: ~4.5 dB
- Solo A1: ~4.5 dB
- Solo A2: ~5.5 dB
- Solo B: ~6.6 dB
- Solo C: ~4.5 dB

The useful learning object is therefore not one average loudness for the tune,
but a **relative contour attached to musical position and phrase role**.

### 4. Accent location changes with role

Using the approximate beat grid, the strongest harmonic-energy beat in the head
falls on beat 2 in 13 of 32 bars, while in the solo it falls on beat 1 in 12 of
32 bars. Attack peaks are distributed across the bar in both phases rather than
being locked to a single metric position.

Because this is mixed audio, these counts should not become a Bill Evans piano
accent prior yet. But they are enough to reject one shared fixed accent table.

### 5. Brightness/register is another independent axis

The harmonic-component spectral centroid rises strongly in the piano-solo
sections relative to the head, especially A2/B. This may reflect higher piano
register, denser upper partials, bass relation or mix contribution.

Therefore brightness/register should condition perceived intensity, but should
not be collapsed into dynamic level.

## Bill Evans hypotheses to test next

These are evidence-driven hypotheses, not promoted Legend tendencies yet.

### H1 — Relative contour survives while absolute level adapts

A phrase may preserve rise/fall identity while the whole contour is shifted
softer or louder according to ensemble density and foreground role.

### H2 — Motif development and dynamic development are coupled but non-monotonic

Possible states include:

- density up + dynamic up
- density up + dynamic down
- space up + body longer
- repeated motif + accent relocation
- climax preparation + temporary dynamic reduction

### H3 — Cadential release is often a change in attack/body relation, not merely volume

Release should be able to reduce accent while lengthening note body or decay.

### H4 — Repetition variation belongs to HOW memory

When the same motif returns, the system should remember recent expression and
avoid replaying the same absolute attack/dynamic stamp.

### H5 — Foreground weight is a shared expressive variable

The Player should know not only how loud to play, but how perceptually foreground
the event should be relative to the ensemble.

## Shared-Core implication

A new shared module is justified:

`src/music_intelligence/expression/`

It owns instrument-neutral HOW intention:

- perceptual intensity
- dynamic level
- accent strength
- note body
- timing emphasis
- foreground weight
- relative phrase contour
- repetition variation

It does **not** own piano velocity, pedal, sax breath pressure, bass pluck, or
drum stroke realization.

The flow becomes:

```
WHAT  Vocabulary / Motif / Phrase
WHEN  MusicalScoreCoordinate
WHY   Harmony / phrase / form / ensemble intention
HOW   Shared Expressive Intelligence
      ↓
Player-specific physical realization
```

## Promotion rule

Do not promote a Bill Evans-specific expression tendency unless it survives:

1. form/score alignment,
2. instrument attribution when required,
3. recurrence across multiple Bill Evans contexts,
4. separation from tune-specific and recording-specific effects.

The current Autumn Leaves analysis is strong enough to guide architecture and
future annotation schema, but not strong enough to claim exact Bill Evans
velocity/accent constants.
