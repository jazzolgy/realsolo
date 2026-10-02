# Bill Evans Trio Role Study — Pass 3: score-position evidence

## Method

This pass re-examines five priority tracks against their supplied lead sheets:
- Waltz For Debby
- Autumn Leaves
- Nardis
- Peri's Scope
- In Your Own Sweet Way

Audio observations come from repeated windowed analysis of the user-provided
compilation (onset activity, spectral centroid, RMS, and coarse HPSS
percussive/harmonic ratio). These are proxies, not isolated drum transcription.

Score observations are kept separate from audio inference.

## 1. Waltz For Debby

### Score evidence
The supplied lead sheet explicitly labels the tune **Medium Jazz Waltz** and
shows A/B/C sections plus a written alternate ending.

### Audio evidence
The strongest non-ending surface changes in the first 100 seconds occur around
50 s and 70 s. Around 70 s the onset rate jumps from roughly 2.7 to 4.3 events/s
and the spectral surface brightens.

### Interpretation hypothesis
The important drummer action near the move away from the opening waltz surface
is not necessarily a fill. A change in cymbal/time surface can communicate a
metric-role transition more economically than a foreground fill.

**Training question:** when meter/feel responsibility changes, can the drummer
change pulse hierarchy before adding density?

## 2. Autumn Leaves

### Score evidence
The project scorebooks contain the standard 32-bar form.

### Audio evidence
The track's local tempo tracker locks near 103 BPM, plausibly a half-time
periodicity for the faster swing surface. Activity is substantially higher in
the middle of the track than the opening. Strong local peaks occur around
150–210 s.

### Interpretation hypothesis
Repeated form does not imply repeated drum behavior. A later chorus can occupy
the same harmonic/form location with a different drummer role because ensemble
history and solo development have changed.

**Training question:** given the same bar/section on chorus N+1, should current
drummer density be conditioned on previous-chorus contribution?

## 3. Nardis

### Score evidence
The supplied lead sheet is marked **Mod. Fast** and contains repeated thematic
material with an internal first/second-ending structure.

### Audio evidence
The track's strongest sustained percussive windows occur much later than the
opening, especially around 210–270 s. This is not a simple linear crescendo;
there are intervening contractions.

### Interpretation hypothesis
The drummer should not derive development merely from elapsed time. Nardis
supports a model in which role can alternate between texture support,
countervoice, and development partner while the underlying tune identity stays
stable.

**Training question:** can the drummer expand orchestration while preserving a
recognizable time surface, then contract without resetting the narrative?

## 4. Peri's Scope

### Score evidence
The supplied chart explicitly contains:
- A head section
- a **solo break**
- a B section labeled **Solos**
- **After solos, D.C. al Coda**
- a written Coda

This is unusually valuable drummer-role evidence because the score states
navigation and role allocation rather than leaving them implicit.

### Audio evidence
The percussive/harmonic ratio is strongest around 105–135 s, while overall
transient activity remains active through much of the solo span. The final
seconds contract sharply.

### Interpretation hypothesis
This tune supports three distinct drummer responsibilities:
1. head support
2. solo-development participation
3. navigation/re-entry support

The transition into B should not be modeled merely as "higher energy."
The **role contract has changed**.

**Training question:** does explicit score role allocation change candidate
ranking even if instantaneous energy is unchanged?

## 5. In Your Own Sweet Way

### Score evidence
The supplied lead sheet explicitly states:

**"Head is in 2 or 4. Solos in 4."**

It also includes A/B/C sections and a separate Coda with straight-eighth
material.

This is direct evidence that meter/pulse realization depends on formal role.

### Audio evidence
The track has a detected periodicity near 152 BPM. High-activity windows cluster
around 100–160 s and again around 300–340 s, rather than remaining stationary
through the performance.

The coarse percussive/harmonic ratio is especially strong around 120–165 s and
300–315 s.

### Interpretation hypothesis
The drummer needs separate concepts for:
- nominal meter
- felt pulse hierarchy
- section role
- solo/head role
- local texture

A 4/4 score does not tell the drummer whether to realize the ensemble in two or
four.

**Training question:** can the drummer change from a lighter two-feel/ambiguous
head support to clear four-beat solo support without treating it as a different
song/style?

## Cross-track conclusion

The strongest repeated lesson is:

**FORM KNOWLEDGE ≠ FORM MARKING**

and

**METER ≠ PULSE RESPONSIBILITY**

A drummer may know the exact form boundary but choose not to mark it.
A drummer may remain in the same notated meter while changing the perceived
pulse hierarchy because the role changes from head support to solo support.

This suggests two Shared-Core concepts that should remain distinct:

- `boundary_confidence`: how sure the system is that a structural boundary is here
- `boundary_marking_need`: how useful it is for this instrument to make that
  boundary perceptually explicit

and two time concepts:

- nominal meter
- pulse-role / felt-beat responsibility

These are research proposals from the Bill Evans comparison, not yet frozen
schema.

## Drummer-role evidence accumulation

Current role candidates remain hypotheses:

- TIME_CLARIFIER
- TEXTURE_SUPPORT
- PHRASE_LISTENER
- COUNTERVOICE
- TRANSITION_AGENT
- DEVELOPMENT_PARTNER
- FOREGROUND_SOLOIST
- RELEASE_SUPPORT

Do not implement these as a closed enum yet. Continue score-aligned evidence
collection and look for repeated transitions among these roles.
