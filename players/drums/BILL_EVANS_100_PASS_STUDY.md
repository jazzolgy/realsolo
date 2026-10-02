# Bill Evans compilation — 100-pass robustness study

## What "100 passes" means

This is not a claim of 100 human auditory listens.

The entire 2:08:37 compilation was analyzed through **100 independent sensitivity
passes**:

- 10 temporal smoothing scales: 1, 2, 3, 4, 6, 8, 10, 12, 16, 20 seconds
- 10 feature-weight profiles spanning transient flux, RMS energy, spectral
  centroid, and high-frequency energy ratio

Every pass covered all 24 supplied track regions.

The purpose is robustness: a musical hypothesis is more interesting when it
survives changes in analysis scale and weighting.

`Peace Piece` and the Bennett/Evans `Some Other Time` are retained in the raw
summary but excluded from the drummer-bearing ensemble consensus.

## Album-level consensus

Mean relative whole-mix activity across the drummer-bearing tracks:

| normalized position | mean | 10th percentile across passes | 90th percentile |
|---|---:|---:|---:|
| 0–10% | -0.394 | -0.488 | -0.289 |
| 10–20% | -0.185 | -0.229 | -0.131 |
| 20–30% | 0.030 | 0.011 | 0.048 |
| 30–40% | 0.110 | 0.102 | 0.117 |
| 40–50% | 0.174 | 0.158 | 0.187 |
| 50–60% | 0.024 | 0.010 | 0.039 |
| 60–70% | -0.013 | -0.034 | 0.009 |
| 70–80% | 0.027 | 0.015 | 0.035 |
| 80–90% | -0.063 | -0.078 | -0.047 |
| 90–100% | -0.395 | -0.495 | -0.302 |

The broad shape survives all 100 parameterizations:

**restrained opening → expansion toward roughly the 30–50% region → variable
middle/late behavior → strong average terminal contraction.**

This is a whole-mix structural proxy, not isolated drummer density. It should
inform hypotheses, not be copied into a fixed drummer envelope.

## Strong repeated track patterns

### Middle expansion survived all 100 passes

The following drummer-bearing tracks had higher middle activity than opening
activity in **100/100** passes:

- Waltz For Debby
- My Foolish Heart
- Autumn Leaves
- Blue In Green
- Someday My Prince Will Come
- The Peacocks
- Spring Is Here
- If You Could See Me Now
- Nardis
- Alice In Wonderland
- How Deep Is The Ocean
- When I Fall In Love
- Peri's Scope
- B Minor Waltz
- Without A Song
- Come Rain or Come Shine
- You Must Believe In Spring
- Garys Theme
- Re: The Person I Knew

This is too consistent to treat "same activity throughout a performance" as a
good default.

### Strong middle → late contraction

Late activity was below middle activity in **100/100** passes for:

- My Foolish Heart
- Autumn Leaves
- Blue In Green
- Someday My Prince Will Come
- The Peacocks
- Spring Is Here
- If You Could See Me Now
- How Deep Is The Ocean
- When I Fall In Love
- Peri's Scope
- B Minor Waltz
- Come Rain or Come Shine
- You Must Believe In Spring
- Garys Theme

Re: The Person I Knew showed the same direction in 95/100 passes.

This does **not** mean "always back off near the end." The exceptions are
musically important.

### Counterexamples: late expansion or non-contraction

- Waltz For Debby: late > middle in 90/100 passes
- Alice In Wonderland: late > middle in 100/100
- Isn't It Romantic: late > middle in 90/100
- Israel: late > middle in 100/100
- In Your Own Sweet Way [Take 1]: late > middle in 100/100
- Nardis: mixed; late > middle in 40/100

Therefore normalized position alone is insufficient. The model needs role,
section, ensemble texture, and narrative state.

## Particularly informative tracks

### Autumn Leaves
Middle expansion survives 100/100 passes and late contraction 100/100.
Mean middle-minus-opening difference is one of the largest in the set (+0.957
relative robust units).

This makes it a strong form-repetition study: later activity is not simply the
same head accompaniment repeated.

### Peri's Scope
Middle expansion 100/100 and late contraction 100/100.
Combined with the chart's explicit solo/navigation evidence, this is a strong
candidate for testing **score role allocation → drummer role → surface activity**.

### Without A Song
Middle expansion survives 100/100 passes, and the activity peak falls in the
last 30% in 82/100 passes. This distinguishes it from most tracks and is
consistent with a performance where drummer foreground ownership becomes
important late in the track.

### Israel
Unlike most tracks, middle activity is lower than opening in all 100 passes and
late activity exceeds middle in all 100. It is a crucial anti-template example:
the system must not assume "open sparse → middle build → ending release."

### In Your Own Sweet Way [Take 1]
Middle is lower than opening in all 100 passes, then late activity exceeds middle
in all 100. The lead-sheet instruction that head and solo use different felt
pulse realization makes this especially important for separating **meter** from
**pulse responsibility**.

### Alice In Wonderland
Middle exceeds opening in all 100 passes, but late exceeds middle in all 100.
It therefore resists a generic terminal-release prior.

## What survives the 100-pass study

The strongest engineering conclusions are:

1. **Drum behavior should be position-aware but not position-determined.**
   Position creates a prior, never a command.

2. **Opening restraint is common but not equivalent to inactivity.**
   It can coexist with clear time responsibility.

3. **Middle expansion is extremely common in this compilation.**
   The drummer needs a development state above immediate comping probability.

4. **Late contraction is common, but counterexamples are strong and repeatable.**
   Ending behavior needs explicit narrative/role evidence.

5. **Same form position can require different realization on later choruses.**
   Form index alone is insufficient.

6. **FORM KNOWLEDGE ≠ FORM MARKING.**
   Boundary confidence and boundary-marking need should remain separable.

7. **METER ≠ PULSE RESPONSIBILITY.**
   Notated meter, felt pulse hierarchy, and drummer time-clarification role are
   separate variables.

8. **Restraint must be role-conditional.**
   A foreground drum-solo allocation can legitimately override a long restraint
   history.

## Proposed next evidence layer — not yet frozen policy

The repeated observations continue to support a drummer-role layer such as:

- TIME_CLARIFIER
- TEXTURE_SUPPORT
- PHRASE_LISTENER
- COUNTERVOICE
- TRANSITION_AGENT
- DEVELOPMENT_PARTNER
- FOREGROUND_SOLOIST
- RELEASE_SUPPORT

But the 100-pass signal study alone cannot assign these semantic labels to every
moment. Those labels should be attached only after score alignment and
source-aware transcription/annotation.

## Important limitation

Transient flux, RMS, centroid, and HF ratios are **whole-mix proxies**.
Piano attack, bass attack, applause, mastering, cymbal energy, and drums all
contribute.

Therefore this study is useful for finding robust structural places to inspect,
not for claiming exact drum-hit counts or exact drummer intentions.
