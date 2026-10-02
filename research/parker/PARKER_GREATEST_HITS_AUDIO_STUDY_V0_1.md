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
