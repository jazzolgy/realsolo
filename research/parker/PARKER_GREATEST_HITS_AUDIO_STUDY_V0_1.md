# Charlie Parker Greatest Hits — Album Audio Study v0.1

## Source

Project audio:

`Charlie Parker Greatest Hits Full Album - The Best Songs Of Charlie Parker.mp3`

Container duration: 6448.056 seconds (~1:47:28).

This document is grounded first in the uploaded audio. It records repeated computational
listening/analysis passes rather than claiming human-style perceptual listening.

## Evidence labels

- AUDIO-OBSERVED: measurable directly in the uploaded waveform/audio features.
- AUDIO-INFERRED: plausible musical interpretation from the mix, not isolated-stem proof.
- PROFILE-CROSSCHECK: consistent with the existing Parker online profile in the project.
- DESIGN-INFERENCE: proposed RealSolo behavior.
- OPEN: requires transcription, stem separation, or expert/manual review.

## Pass 1 — Large-scale segmentation

FFmpeg silence detection found many clear inter-track gaps, including boundaries around:

- 178–181 s
- 359–363 s
- 527–531 s
- 740–744 s
- 924–936 s
- 2444–2451 s
- 2847–2855 s
- 3138–3142 s
- 3702–3708 s
- 3895–3899 s
- 4629–4633 s
- 4806–4814 s
- 5177–5182 s
- 5357–5365 s
- 6059–6067 s
- 6249–6257 s
- final fade/silence near 6442 s

Additional spectral-novelty peaks exist between those gaps, so silence alone is not
sufficient for final track indexing.

### AUDIO-OBSERVED

The compilation contains strongly differentiated local textures rather than one uniform
bebop surface.

Early likely-track segments already show large changes in onset density and harmonic /
percussive balance.

## Pass 2 — Track-level feature probes

Representative early segments:

| Segment | Approx interval | Tempo proxy | Onsets/sec | Harmonic/percussive RMS ratio | Activity variation |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 0–180 s | ~108 | 3.87 | 1.18 | moderate |
| 2 | 180–361 s | ~118 | 2.29 | 0.95 | low |
| 3 | 361–529 s | ~118 | 1.84 | 1.92 | high |
| 4 | 529–742 s | ~129 | 3.10 | 1.37 | medium-high |
| 5 | 742–930 s | ~99 | 3.83 | 1.54 | moderate |
| 6 | 930–1112 s | ~108 | 3.96 | 1.07 | low-moderate |

Tempo values are automated proxies and may reflect half/double-time ambiguity.

### DESIGN IMPLICATION

The initial bebop piano solo grammar must not map “bebop” to a fixed event density.
Density must remain phrase-, tune-, and ensemble-dependent.

## Pass 3 — Four 45-second representative windows

Technical windows were extracted at approximately:

- A: 45–90 s
- B: 390–435 s
- C: 600–645 s
- D: 980–1025 s

Measured behavior:

### Window A
- tempo proxy ~101
- ~4.8 detected onsets/sec
- median ~3 detected onsets/beat
- strong harmonic energy relative to percussive energy
- comparatively stable chroma-change profile

### Window B
- tempo proxy ~144
- ~1.2 detected onsets/sec
- many beat windows with no strong detected onset
- strongest harmonic/percussive ratio of the four
- demonstrates that a faster pulse can coexist with relatively sparse salient attacks

### Window C
- tempo proxy ~136
- ~2.3 detected onsets/sec
- intermediate density
- larger chroma-change peaks than A/B

### Window D
- tempo proxy ~106
- ~5.0 detected onsets/sec
- median ~3 detected onsets/beat
- lower harmonic/percussive ratio than A/B

### AUDIO-OBSERVED

Fast pulse does not imply high salient-event density.

This directly supports the existing RealSolo principle learned from comping research:
surface speed and musical event rate must remain separate variables.

## Pass 4 — Parker melodic-prior crosscheck

The existing project profile `PARKER_ONLINE_PROFILE` contains immediate-decision
preferences for:

- anticipation
- passing motion
- neighbor motion
- close approaches
- directed altered color
- audible resolution paths
- contextual triplets
- ensemble space
- syncopated long tones
- restraint against routine beat-1 holds
- restraint against repeated wide leaps

### PROFILE-CROSSCHECK

The uploaded compilation's large differences in local density and attack activity are
compatible with a Parker model based on conditional choices rather than constant
high-density scalar motion.

The audio does **not** by itself prove each profile tendency; those tendencies remain
grounded in the profile's existing Omnibook/book/expert provenance.

## Pass 5 — Ensemble / pianist role study

### AUDIO-OBSERVED

The full mix exhibits recurring changes in:
- attack density
- harmonic vs percussive dominance
- local dynamic range
- silence/fade boundaries
- chroma-change rate
- likely section/solo texture

### OPEN / LIMITATION

The uploaded stereo mix does not provide a reliable isolated piano stem.

An attempted Demucs separation could not run because model weights were not available
in the offline environment.

Therefore the following must **not** yet be promoted as direct audio facts:
- exact piano comping rhythm
- exact piano voicing content
- which individual response was initiated by piano versus another rhythm-section player
- note-level call/response attribution between Parker and pianist

### AUDIO-INFERRED research targets

For later manual/transcription crosscheck, mark passages where:
- full-band onset density drops while harmonic energy remains strong;
- Parker-like high melodic activity is followed by lower ensemble attack density;
- dense full-band attacks give way to sustained harmonic beds;
- section changes coincide with clear changes in rhythmic support.

These are candidate regions for studying:
- pianist lay-out
- sustained support
- punctuation
- rhythmic handoff
- soloist/comping density complementarity

## Bebop solo implications for Piano Player

### DESIGN-INFERENCE

Initial piano solo behavior should use Parker as a melodic decision prior, while keeping
piano realization independent.

The system should preserve:

1. Harmonic target awareness
   - guide-tone/chord-tone arrivals
   - directed chromatic approaches
   - altered notes with audible destination

2. Phrase motion
   - passing/neighbor/enclosure-like connectivity
   - anticipation of future harmony
   - variable phrase density
   - rests as structural material

3. Rhythmic character
   - offbeat/anticipated entry
   - contextual triplets
   - syncopated sustained notes
   - avoidance of monotonous beat-1 long-tone repetition

4. Contour discipline
   - wide leaps as events, not default locomotion
   - recovery/connective motion after large leaps

5. Ensemble awareness
   - do not maintain maximal melodic density merely because bebop tempo is high
   - allow rhythm section space
   - adjust right-hand density to left-hand comping and ensemble activity

## Ensemble implications

### DESIGN-INFERENCE

RealSolo should eventually represent bebop ensemble interaction as at least:

```
soloist melodic activity
+ soloist phrase boundary
+ drums accent/setup activity
+ bass continuity/activity
+ piano harmonic coverage
+ piano rhythmic coverage
+ recent response episode
```

The pianist should be capable of:
- laying out under saturated solo phrases;
- supplying compact harmonic identity when needed;
- punctuating phrase holes;
- preserving pulse/groove without mechanically matching every Parker event;
- responding after phrase endings rather than continuously shadowing the soloist.

These remain design hypotheses until transcription/stem evidence confirms specific
Parker-recording examples.

## Next audio passes

1. refine track boundaries using silence + spectral novelty;
2. rank segments by event density and harmonic/percussive balance;
3. cross-reference selected passages with Parker transcriptions where available;
4. annotate phrase-space windows;
5. annotate ensemble-density transitions;
6. build a piano-role evidence set with confidence/provenance;
7. compare Parker solo activity with likely accompaniment-density changes;
8. only then calibrate numeric solo/comping interaction weights.

## Non-copying rule

The uploaded album is used to learn conditional musical behavior and ensemble grammar.

RealSolo must not memorize and replay complete Parker solos or literal future phrase
sequences.

The runtime invariant remains:

`Plan intention, not notes.`


## Pass 6 — Phrase-space / activity-transition scan

A second whole-album pass used 250 ms blocks and a robust activity score combining:

- RMS energy
- time-domain attack/flux proxy
- zero-crossing rate

After 1-second smoothing, the lower 20% and upper 20% activity regions were compared.

### AUDIO-OBSERVED

- 373 low-activity runs of roughly 1–8 seconds were detected outside obvious full-track silence.
- 118 of those were adjacent to substantially higher activity before or after them and
  are candidate **phrase-space / handoff transition** regions.
- Examples include transitions around:
  - 397.75–398.75 s
  - 428.75–429.75 s
  - 433.00–435.25 s
  - 1308.00–1310.75 s
  - 1313.25–1315.50 s
  - 1355.25–1356.75 s
  - 1365.75–1367.00 s
  - 1386.25–1387.50 s
  - 1549.25–1551.50 s
  - 2008.00–2010.75 s

The 1109–1114 s region is a likely track boundary rather than an intra-performance
phrase-space event and must be excluded from interaction learning.

### AUDIO-INFERRED

The high count of short low-activity windows is consistent with bebop performance
containing many brief reductions in surface density rather than continuous maximal
activity.

However, the full mix cannot yet say whether each window represents:
- Parker resting;
- piano laying out;
- a drummer/bass texture change;
- a sustained note;
- a formal break;
- or several of these simultaneously.

### DESIGN-INFERENCE

RealSolo should not model phrase space as binary silence only.

Useful future state:

```
phrase_space_window
  duration
  activity_drop
  pre_activity
  post_activity
  actor_confidence
  provenance
```

This can support:
- soloist breath / release detection;
- pianist answer windows;
- ensemble handoff;
- density recovery;
- intentional sustained-note space.

Actor attribution must remain separate from the raw activity transition.


## Pass 7 — Exact morphology of selected phrase-space candidates

Ten previously detected low-activity regions were re-extracted with exactly:

```
1 second before
+ detected low-activity interval
+ 1 second after
```

For each region, RMS energy and short-time spectral-flux proxy were compared.

### AUDIO-OBSERVED

Selected results:

| Region (s) | Low RMS / pre RMS | Low RMS / post RMS | Low flux / pre flux | Low flux / post flux | Interpretation status |
| --- | ---: | ---: | ---: | ---: | --- |
| 397.75–398.75 | 0.65 | 0.31 | 1.26 | 1.22 | quiet-active candidate |
| 428.75–429.75 | 0.68 | 0.35 | 0.96 | 1.01 | quiet-active candidate |
| 433.00–435.25 | 0.58 | 0.41 | 1.18 | 0.99 | quiet-active candidate |
| 1308.00–1310.75 | 0.56 | 0.37 | 1.02 | 1.27 | quiet-active candidate |
| 1313.25–1315.50 | 0.46 | 0.22 | 0.90 | 0.77 | stronger release candidate |
| 1355.25–1356.75 | 0.37 | 0.18 | 1.09 | 1.09 | quiet-active despite deep energy drop |
| 1365.75–1367.00 | 0.62 | 0.15 | 1.09 | 0.90 | quiet-active / strong re-entry contrast |
| 1386.25–1387.50 | 0.46 | 0.23 | 0.89 | 1.20 | quiet-active candidate |
| 1549.25–1551.50 | 0.50 | 0.23 | 1.16 | 1.05 | quiet-active candidate |
| 2008.00–2010.75 | 0.31 | 0.19 | 0.72 | 0.76 | strongest deep-release candidate |

The key observation is that **energy reduction and attack reduction are not the same
thing**.

Several regions lose substantial RMS energy while the spectral-flux proxy remains at
or above the surrounding level. Those regions should not be represented as simple
silence.

The 2008–2011 s region is qualitatively different in this feature space: both energy
and attack/flux proxies fall substantially, followed by a much stronger post-region
energy level.

### DESIGN-INFERENCE

Phrase-space should therefore distinguish at least:

- `QUIET_ACTIVE`
  - lower energy
  - internal attack/motion may continue
  - do not automatically fill the space
  - dense solo re-entry may erase useful ensemble texture

- `DEEP_RELEASE`
  - large energy drop
  - attack activity also decreases
  - can create a clearer pickup/re-entry opportunity
  - still does not require immediate playing

This distinction is now implemented experimentally in:

`players/piano/bebop_phrase_space.py`

and consumed by the Parker-prior piano solo policy.

### Attribution caution

None of these classifications identifies **which musician** created the space.

The raw evidence is ensemble-level.

`actor_attribution_confidence` therefore defaults to zero until stronger evidence is
available.


## Pass 8 — Harmonic vs percussive persistence inside phrase space

The same ten selected phrase-space candidates were analyzed with HPSS
(harmonic/percussive source decomposition). This is **not instrument separation**:
the percussive component is not equivalent to an isolated drum stem.

### AUDIO-OBSERVED

Several low-energy regions preserve or even increase the percussive component relative
to the preceding second while harmonic energy falls.

Examples:

| Region (s) | Harmonic low/pre | Percussive low/pre | Harmonic low/post | Percussive low/post |
| --- | ---: | ---: | ---: | ---: |
| 397.75–398.75 | 0.54 | 1.12 | 0.33 | 0.22 |
| 428.75–429.75 | 0.60 | 1.51 | 0.48 | 0.25 |
| 1308.00–1310.75 | 0.48 | 0.82 | 0.28 | 0.96 |
| 1365.75–1367.00 | 0.39 | 1.75 | 0.11 | 0.25 |
| 2008.00–2010.75 | 0.31 | 0.30 | 0.16 | 0.25 |

The 397.75, 428.75, and 1365.75 s candidates are particularly important:
the harmonic component becomes much thinner while percussive activity remains strong.

The 2008–2011 s candidate is different: both harmonic and percussive components reduce
substantially.

### AUDIO-INFERRED

Some bebop phrase-space windows therefore appear better described as:

```
melodic/harmonic thinning
while a pulse/attack layer remains active
```

rather than:

```
the entire ensemble stops
```

The mix alone does not identify whether the persistent percussive component is drums,
bass attack, piano attack, recording artifact, or a combination. Actor attribution
remains open.

### DESIGN-INFERENCE

Phrase-space evidence now preserves separate:

- `harmonic_support`
- `percussive_support`

For piano solo policy:

- quiet-active space with strong percussive support does not need to be filled;
- if the pianist re-enters, an anticipation/pickup/syncopated entry may fit better than
  a heavy downbeat restart;
- deep release with weak percussive support permits a more explicit phrase reset.

This is an ensemble-interaction prior, not a Parker lick rule.


## Pass 9 — Foreground/support complementarity around selected breath regions

A further focused pass compared three proxies around selected candidate regions:

- upper harmonic activity / flux as a **foreground melodic proxy**;
- low harmonic energy as a **low harmonic support proxy**;
- HPSS percussive energy as a **percussive support proxy**.

These remain mixed-signal proxies, not isolated instrument stems.

### AUDIO-OBSERVED

Selected examples:

| Region start (s) | Foreground during/pre | Low harmonic support during/pre | Percussive support during/pre | Foreground post/during |
| --- | ---: | ---: | ---: | ---: |
| 428.75 | 0.47 | 0.98 | 1.04 | 5.79 |
| 433.00 | 0.18 | 0.79 | 0.44 | 2.81 |
| 1308.00 | 0.07 | 0.51 | 0.72 | 5.03 |
| 1313.25 | 0.08 | 0.95 | 0.58 | 10.79 |
| 1355.25 | 0.08 | 0.75 | 0.42 | 35.04 |
| 1365.75 | 0.11 | 0.53 | 1.30 | 21.04 |
| 1386.25 | 0.18 | 0.90 | 1.00 | 6.21 |
| 1549.25 | 0.33 | 0.46 | 0.47 | 7.50 |
| 2008.00 | 0.17 | 0.30 | 0.68 | 3.10 |

### AUDIO-OBSERVED pattern

There are at least two recurring morphological possibilities in this sample:

#### Foreground handoff

Foreground activity drops strongly while one or more support proxies remain relatively
high.

Strong examples include:

- 1313.25 s: foreground ~8% of pre, low harmonic support ~95%;
- 1365.75 s: foreground ~11%, percussive support ~130%;
- 1386.25 s: foreground ~18%, low harmonic ~90%, percussive ~100%.

#### Collective release

Foreground and support layers both thin substantially.

The 2008.00 s region is the clearest selected example:
foreground ~17%, low harmonic support ~30%, percussive support ~68%.

### AUDIO-INFERRED

These patterns are consistent with a bebop ensemble distinction between:

```
foreground voice backs away
while rhythm/harmony continues
```

and:

```
the ensemble collectively releases
```

The audio mix does not identify whether the foreground proxy is always Parker, nor
which instrument supplies the persistent support.

### DESIGN-INFERENCE

RealSolo now represents this distinction experimentally as:

- `FOREGROUND_HANDOFF`
- `COLLECTIVE_RELEASE`
- `COLLECTIVE_BUILD`
- `NONE`

in `players/piano/bebop_complementarity.py`.

Piano-solo consequences:

- foreground handoff can remain open;
- active support can favor a light pickup/anticipation rather than a dense restart;
- dense runs can be penalized if they erase an already-supported handoff;
- collective release can frame a new directed phrase entry, but still need not be filled.

Piano-comping consequences:

- if accompaniment support already carries a foreground handoff, lay-out or brief
  punctuation can be preferable to sustained harmonic filling;
- collective release can be preserved rather than overwritten by immediate sustained
  comping.

This is ensemble-interaction grammar, not a literal Parker phrase rule.


## Pass 10 — Fixed-window turn-taking episode probe

Nine selected candidate regions were re-analyzed with a fixed temporal morphology:

```
3 s pre
+ 2 s candidate handoff
+ 3 s post
```

The proxies in this pass were intentionally simple and reproducible:

- 500–2500 Hz spectral energy as a mid-band foreground proxy;
- 60–500 Hz energy as a low harmonic/support proxy;
- broadband positive spectral flux as an attack/activity proxy.

### AUDIO-OBSERVED

| Region start (s) | Foreground handoff/pre | Low support handoff/pre | Attack handoff/pre | Foreground post/handoff | Provisional morphology |
| --- | ---: | ---: | ---: | ---: | --- |
| 428.75 | 0.87 | 1.19 | 0.97 | 1.16 | ambiguous / weak handoff |
| 433.00 | 0.18 | 0.81 | 0.38 | 4.87 | supported handoff + re-entry |
| 1308.00 | 0.14 | 0.65 | 0.73 | 6.39 | supported handoff + re-entry |
| 1313.25 | 0.13 | 0.88 | 0.48 | 12.02 | supported handoff + strong re-entry |
| 1355.25 | 0.77 | 1.02 | 0.82 | 4.19 | ambiguous / transition mixed into window |
| 1365.75 | 2.06 | 0.73 | 1.79 | 0.86 | foreground continues in fixed 2-s window |
| 1386.25 | 0.54 | 1.21 | 0.76 | 1.73 | ambiguous |
| 1549.25 | 0.25 | 0.52 | 0.45 | 9.69 | collective-release-like + re-entry |
| 2008.00 | 0.19 | 0.38 | 0.24 | 5.41 | strong collective release + re-entry |

### AUDIO-OBSERVED / methodological caution

The fixed-window result at **1365.75 s** differs from the earlier boundary-aligned
low-activity analysis.

Earlier, the detected low-activity interval itself showed very low foreground/harmonic
energy while percussive support remained strong.

When the handoff window is forcibly extended to two seconds, later re-entry activity is
mixed into the same window and the foreground ratio rises above 2.0.

This means:

```
fixed-duration window
!=
true handoff interval
```

for some episodes.

### DESIGN-INFERENCE

Runtime turn-taking analysis should prefer **boundary-aligned phrase-space intervals**
over arbitrary fixed handoff durations.

Recommended morphology:

```
pre context
-> detected handoff interval (variable duration)
-> detected re-entry / post context
```

rather than:

```
pre 3 s
-> always 2 s handoff
-> post 3 s
```

Fixed windows remain useful for offline comparison and regression tests, but should not
be treated as the primary musical segmentation model.

### Experimental episode types

The piano-side research adapter now distinguishes:

- `SUPPORTED_HANDOFF_REENTRY`
- `COLLECTIVE_RELEASE_REENTRY`
- `FOREGROUND_CONTINUES`
- `AMBIGUOUS`

These classify an **already observed** episode and contain no prediction of the next
phrase.
