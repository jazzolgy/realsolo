# Bebop Evidence Matrix

This file separates claims by evidence type so that the drummer model does not
confuse listening impressions, teaching-method abstractions, historical facts,
and implementation hypotheses.

## Evidence classes

### A — Direct uploaded-audio observation
Derived from the user-supplied 107.5-minute Charlie Parker compilation.  These
claims may describe audible/measureable behavior but not personnel unless a
recording is independently identified.

### B — Uploaded method-book support
Derived from specific uploaded drum books.  This describes pedagogical grammar,
not proof that every Parker recording uses the same behavior.

### C — External historical verification
Derived from institutional/history/discography sources.

### D — Engineering hypothesis
A RealSolo modeling proposal that still requires musical validation.

---

## Ride cymbal

**Claim:** bebop time is ride-led rather than bass-drum-led.

- A: The compilation consistently presents an upper-cymbal time layer that
  remains perceptually central while other kit activity changes.
- B: Riley begins bop time-playing with ride-cymbal phrasing and treats the
  quarter-note pulse as the basis of forward motion.
- C: Smithsonian describes Kenny Clarke as moving the timekeeping role from bass
  drum to ride cymbal, freeing kick/snare for accent and rhythmic stimulus.
- D: Model ride as a continuity field plus variable surface grammar.

**Claim:** the familiar skip-beat is vocabulary, not a compulsory repeating cell.

- A: Broad listening suggests variable quarter-note/skip-note emphasis rather
  than a perfectly repeated two-beat loop.
- B: Riley presents several notational approximations and emphasizes pulse and
  phrasing rather than literal notation.
- D: Store source patterns but permit omission, extension, accent displacement,
  and quarter-note-dominant variants.

---

## Bass drum

**Claim:** quiet pulse support and isolated accents are different intentions.

- B: Riley distinguishes soft quarter-note bass-drum playing from more active
  bass-drum comping.
- C: historical descriptions of bebop drumming distinguish timekeeping from
  accent/bomb usage after the ride takes over the primary clock.
- D: split `FLOOR_SUPPORT`, `INTERACTIVE_ACCENT`, and
  `ENSEMBLE_FIGURE_SUPPORT`.

The uploaded mix alone is not sufficient to label every low-frequency event as
bass drum because bass instrument energy overlaps strongly.  Drum-stem or expert
transcription is required before training event-level bass-drum probabilities.

---

## Hi-hat

**Claim:** pedal hi-hat 2&4 is a strong bebop anchor.

- B: Riley explicitly teaches hi-hat on 2 and 4 as a stable time foundation.
- A: portions of the compilation support a recurring metrical hi-hat layer, but
  recording quality prevents reliable automatic event extraction in all tracks.
- D: encode 2&4 as a high-probability style prior with omission/dynamic controls,
  not an invariant rule.

---

## Snare comping

**Claim:** snare accompaniment should be modeled as musical dialogue.

- B: Riley states comping functions including enhancing groove, adding variety,
  supporting/stimulating the soloist, and responding to another player.
- B: Riley explicitly warns against disrupting flow or overstimulating the
  soloist.
- A: broad listening is consistent with selective rather than continuous snare
  commentary.
- D: assign each comp event an interaction intention rather than sampling a
  style pattern independently.

---

## Pacing and silence

**Claim:** comping needs phrase-scale memory.

- B: Riley's pacing and rhythmic-transposition work deliberately spaces ideas and
  repositions recognizable rhythmic material over longer phrases.
- A: audible drum activity is not uniformly dense across the compilation.
- D: track recent comp density, time since last statement, motif position, and
  intentional non-response.

---

## Soloist energy interaction

**Claim:** drummer density should not be a monotonic function of soloist density.

- B: Riley explicitly distinguishes building with a soloist, coming down from a
  climax, and coasting while the soloist builds.
- D: implement a discrete/continuous interaction-state estimator:
  LISTEN, SUPPORT, BUILD, COAST, COME_DOWN, RELEASE.

This is one of the highest-priority changes to the current prototype.

---

## Form

**Claim:** form awareness enables freedom but does not mandate fills.

- B: Riley's listening/song-structure section explicitly trains 12-bar blues and
  32-bar song-form awareness.
- D: section/phrase boundary raises opportunity for punctuation; it does not
  trigger an obligatory fill.

---

## Four-limb relationship

**Claim:** musical interdependence is more useful than four independent limb
generators.

- B: Riley explicitly frames the limbs as interdependent in musical use.
- D: musical intention must precede orchestration and limb assignment.

---

## Bass/drum relationship

**Claim:** ensemble lock is not equivalent to simultaneous attacks.

- C: historical bebop descriptions emphasize a larger foundational pulse role
  for bass while drums gain surface freedom.
- A: the uploaded recordings are consistent with continuous bass motion plus a
  more variable drum surface.
- D: score bass/drum interaction using shared pulse, phase, complementary
  density, directional energy, and selective accent alignment.

---

## Drummer identity and Parker sessions

Historical session records verify substantial Charlie Parker work with Max Roach,
including the May 8, 1947 Savoy session (Donna Lee, Chasin' the Bird and related
takes), August 14, 1947 material with Parker in Miles Davis' All Stars, September
1948 Parker All Stars sessions, and numerous Royal Roost broadcasts.

This does **not** establish that any unidentified timestamp in the uploaded
compilation is Max Roach.  Track identification must precede LegendProfile
attribution.

---

## Quantitative audio survey

Silence detection at -38 dB / >=1 s produced a set of robust boundaries, but
long regions remain where multiple recordings may be joined without sufficient
silence.  Therefore the compilation currently has 22 **track-like analysis
regions**, not 22 asserted tracks.

Each region was sampled at early/middle/late 20-second windows.  Features:
- onset event rate from percussive HPSS component;
- selected pulse periodicity;
- relative high/mid/low percussive spectral energy;
- RMS level.

The pulse detector often chooses half-time in jazz.  Values are retained as
`pulse_periodicity_bpm`, never treated as verified tune BPM.

---

## What requires expert/manual listening next

1. Select high-confidence track-like regions of ~3 minutes.
2. Annotate 8-bar excerpts by hand:
   - beat/quarter-note reference
   - ride hit / skip / omission / accent
   - pedal hi-hat confidence
   - snare comping
   - bass drum floor/accent only when audible
   - phrase boundaries
   - horn density/phrase ending
   - setup/handoff
3. Re-listen without notation and classify:
   - BUILD / COAST / COME_DOWN
   - answer / non-response
4. Compare the symbolic transcription to the audible musical effect.
5. Only then estimate probability distributions for BebopStyleProfile.

The target is not to extract the maximum number of notes; it is to discover the
conditional choices that make the drummer sound like an intelligent bebop
musician.
