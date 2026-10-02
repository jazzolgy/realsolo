# Bill Evans Compilation — 1000-Pass Analysis v0.1

## Scope

Source audio:
- uploaded Bill Evans compilation
- total duration: approximately 7717.956 seconds
- 24 user-identified tracks

This pass does **not** claim 1000 human listen-throughs.

It executes exactly 1000 deterministic analysis windows across the complete compilation,
allocated approximately in proportion to track duration. Each pass is a 10-second
window and measures ensemble-level audio features.

Important limitation:
the source is a stereo mix, not isolated stems. Therefore no window-level metric is
treated as proof of a specific piano, bass, or drum action.

## 1000-pass allocation

The 24 tracks received between 33 and 53 windows each, totaling exactly 1000.

Representative counts:

- Waltz For Debby: 48
- Autumn Leaves: 44
- Blue In Green: 42
- Alice In Wonderland: 48
- How Deep Is The Ocean: 35
- Peri's Scope: 33
- Come Rain or Come Shine: 34
- Re: The Person I Knew: 43

## Features per pass

Each window measured:

- RMS / overall level proxy
- dynamic coefficient of variation
- positive short-frame energy change / onset-change proxy
- low-activity proportion / space proxy
- spectral centroid
- low-frequency energy ratio
- low-mid energy ratio
- high-frequency energy ratio
- spectral flatness
- short-range envelope periodicity

These are deliberately low-level observations. Musical interpretation is kept separate.

## Unsupervised texture grouping

Five coarse audio texture clusters emerged.

These are descriptive acoustic groups, not instrument labels.

### Cluster 0
- strong low-frequency energy
- relatively active transient behavior
- lower spectral centroid

### Cluster 1
- active mid-density texture
- moderate dynamics
- stronger low-mid energy

### Cluster 2
- brighter/high-frequency texture
- higher spectral centroid
- stronger high-frequency ratio

### Cluster 3
- sparse / high-dynamic-contrast texture
- high dynamic variability
- lower RMS
- relatively strong periodicity

### Cluster 4
- steadier low-register-weighted texture
- lower onset-change activity
- moderate periodicity

## Large cross-track differences

### Blue In Green

42 passes.

Median:
- dynamic CV: ~0.706
- onset-change proxy: ~0.063
- low-activity ratio: ~0.107
- periodicity: ~0.514

Texture distribution:
- ~83% cluster 3

Interpretation:
this performance is acoustically dominated by a sparse/high-contrast texture compared
with the more active swing tracks.

This does **not** imply "Bill Evans always plays sparsely."

### Autumn Leaves

44 passes.

Median:
- dynamic CV: ~0.460
- onset-change proxy: ~0.080
- low-activity ratio: ~0.099
- periodicity: ~0.299

Texture distribution:
- ~77% cluster 1

Interpretation:
substantially more active and less dynamically extreme than Blue In Green.

### Peri's Scope

33 passes.

Median onset-change proxy: ~0.082.

Texture distribution:
- ~88% cluster 1
- ~12% cluster 3

Interpretation:
active harmonic/rhythmic texture is a stable feature of this recording relative to
Blue In Green.

### Alice In Wonderland

48 passes.

Texture distribution:
- ~52% cluster 1
- ~31% cluster 0
- ~12% cluster 4

Interpretation:
3/4 does not map to one acoustic texture. The performance moves across active,
low-register-weighted and steadier states.

### How Deep Is The Ocean

35 passes.

Texture distribution:
- ~71% cluster 4

Interpretation:
a comparatively steady, low-register-weighted ensemble texture dominates much of the
recording.

### Come Rain or Come Shine

34 passes.

Texture distribution:
- ~53% cluster 3
- ~26% cluster 1
- ~18% cluster 4

Interpretation:
the performance mixes sparse/high-contrast and active harmonic textures rather than
remaining in one density mode.

## Early / middle / late behavior

The same track often changes texture over time.

Examples:

### Waltz For Debby
median onset-change:
- early ~0.060
- middle ~0.074
- late ~0.085

### Blue In Green
median onset-change:
- early ~0.050
- middle ~0.069
- late ~0.059

late low-activity rises to ~0.153.

### Alice In Wonderland
median onset-change:
- early ~0.064
- middle ~0.081
- late ~0.066

### Come Rain or Come Shine
median onset-change:
- early ~0.062
- middle ~0.072
- late ~0.058

### Nardis
median onset-change:
- early ~0.082
- middle ~0.096
- late ~0.060

These observations support a capability for long-range density shaping, but they do not
prove a universal Evans "arch" formula.

## Source-book cross-check

The analytical books strengthen several implementation hypotheses.

### Peri's Scope

The Reilly analysis treats compact structural voicings and added color tones as a
systematic vocabulary, including extensions and altered colors.

Implementation consequence:
Piano needs multiple LH texture densities rather than shell-only default behavior.

### Time Remembered

The source separates harmonic, modal and intervallic analysis and studies multiple
voicing categories/inversions.

Implementation consequence:
consecutive voicings should be evaluated as connected voices, not unrelated chord
grips.

### How Deep Is The Ocean

The Reilly analysis presents a reharmonized Evans progression with persistent 9th,
11th, 13th and altered extension language.

Implementation consequence:
harmonic color density must be separable from rhythmic attack density.

### B Minor Waltz

The analytical material treats several simultaneous parts as distinct voices and
encourages horizontal/contrapuntal understanding.

Implementation consequence:
LH comping needs voice-leading and inner-line continuity, not only chord labels.

## Evidence taxonomy

No observation is promoted automatically to generic jazz-piano law.

Use:

- EVANS_OBSERVED
- EVANS_ANALYST_INTERPRETATION
- EVANS_STABLE_TENDENCY
- EVANS_CONTEXTUAL_TENDENCY
- CROSS_PIANIST_CONFIRMED
- GENERIC_PIANO_CANDIDATE

Multiple Evans tracks can establish an Evans-stable tendency but **not** genericity.

## Implementation consequences already completed

### 1. LH texture classes

Runtime now distinguishes:

- LAY_OUT
- SINGLE_STRUCTURAL
- GUIDE_DYAD
- ROOT_ANCHOR
- ONE_TENSION
- TWO_TENSION
- ALTERED_COLOR
- SUSTAINED_COLOR

### 2. One- and two-tension rootless candidates

Both are ordinary candidate sources when Shared Harmony supplies the pitch roles.

### 3. Root anchor

A root-only structural gesture is available but is discouraged when an active bassist
already owns the root.

### 4. LH voice-leading memory

Candidate evaluation now considers:

- common tones
- nearest-voice motion
- average movement
- LH top-note trajectory
- large grip jumps

### 5. RH ownership

In piano-led trio mode:
- RH owns melody/solo foreground
- LH owns accompaniment role
- silence remains a valid LH action

## Next executable requirement

The next missing behavior is not another voicing family.

It is explicit **RH-LH rhythmic relationship**.

Runtime should distinguish:

- simultaneous support
- delayed response
- phrase-gap answer
- sustained color under RH line
- intentional rhythmic doubling
- lay-out

Crucially:

```
busy RH != always silence
```

and:

```
simultaneous RH/LH attack != automatically good comping
```

Intentional doubling should require strong rhythmic/motivic evidence.

This should be implemented as current-tick evaluation only, never a frozen future
two-hand phrase.
