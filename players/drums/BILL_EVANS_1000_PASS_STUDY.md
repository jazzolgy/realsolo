# Bill Evans compilation — 1000-pass robustness study

## Definition of 1000 passes

This is **not** a claim of 1000 human auditory listens.

The entire 2:08:37 source was re-analyzed through exactly 1000 deterministic
sensitivity passes:

- 20 smoothing windows: 1–20 seconds
- 10 feature-weight profiles
- 5 track-boundary perturbations: -2, -1, 0, +1, +2 seconds

Each pass used the whole compilation and the supplied 24-track timeline.

Base features were computed at one-second resolution from the local 8 kHz mono
analysis copy:
- RMS energy
- zero-crossing rate
- spectral centroid
- high-frequency / low-mid energy ratio
- positive spectral flux

Features were robust-normalized within each track before weighting.

`Peace Piece` and Bennett/Evans `Some Other Time` remain in the per-track table
but are excluded from the drummer-bearing album consensus.

## 1000-pass album consensus

Across drummer-bearing tracks, the mean normalized whole-mix activity trajectory
was:

| position | mean | P10 | P90 | positive in passes |
|---|---:|---:|---:|---:|
| 0–10% | -0.374 | -0.647 | -0.191 | 0.0% |
| 10–20% | -0.124 | -0.168 | -0.065 | 0.0% |
| 20–30% | +0.132 | +0.094 | +0.179 | 100.0% |
| 30–40% | +0.234 | +0.196 | +0.277 | 100.0% |
| 40–50% | +0.332 | +0.299 | +0.367 | 100.0% |
| 50–60% | +0.145 | +0.110 | +0.192 | 100.0% |
| 60–70% | +0.119 | +0.076 | +0.171 | 100.0% |
| 70–80% | +0.162 | +0.123 | +0.205 | 100.0% |
| 80–90% | +0.027 | -0.009 | +0.075 | 81.1% |
| 90–100% | -0.472 | -0.892 | -0.133 | 0.0% |

The most robust whole-set pattern is therefore:

**restrained first fifth → expansion by 20–30% → broad activity plateau through
roughly 80% → strong final-decile contraction.**

This is a whole-mix structural tendency, not a drum-density template.

## What survived 1000/1000

### Middle > opening in every pass

The following drummer-bearing tracks showed higher middle activity than opening
activity in all 1000 passes:

- Waltz For Debby
- My Foolish Heart
- Autumn Leaves
- Blue In Green
- Someday My Prince Will Come
- The Peacocks
- Spring Is Here
- If You Could See Me Now
- Alice In Wonderland
- How Deep Is The Ocean
- When I Fall In Love
- Isn't It Romantic
- Peri's Scope
- B Minor Waltz
- Without A Song
- Come Rain or Come Shine
- Garys Theme
- Re: The Person I Knew

Notable exceptions:
- Nardis: 0/1000
- In Your Own Sweet Way [Take 1]: 0/1000
- Israel: 308/1000
- You Must Believe In Spring: 855/1000

These exceptions are as important as the consensus.

### Late < middle in every pass

1000/1000 late contraction occurred in:

- Waltz For Debby
- Autumn Leaves
- Blue In Green
- Someday My Prince Will Come
- Spring Is Here
- How Deep Is The Ocean
- When I Fall In Love
- Peri's Scope
- B Minor Waltz
- Without A Song
- Come Rain or Come Shine
- Garys Theme
- Re: The Person I Knew

Near-consensus contraction:
- If You Could See Me Now: 990/1000
- The Peacocks: 980/1000
- My Foolish Heart: 928/1000
- Isn't It Romantic: 890/1000

Robust counterexamples:
- Nardis: late > middle 1000/1000
- In Your Own Sweet Way: late > middle 1000/1000
- Israel: late > middle 847/1000
- Alice In Wonderland: late > middle 799/1000
- You Must Believe In Spring: essentially split, 502/1000 late > middle

## Most important revision from the 100-pass study

The 1000-pass analysis overturns some conclusions from the smaller sensitivity
set.

Most notably, `Waltz For Debby` is now **late < middle in 1000/1000** passes
under the broader feature family, whereas the earlier 100-pass study suggested
late expansion.

This means the earlier statement was not robust enough and should not be used as
a training rule.

This is exactly why repeated sensitivity analysis matters:
**a behavior should not enter policy merely because one analysis configuration
supports it.**

## Track-level structural archetypes

The 1000 passes reveal several recurring but non-universal shapes.

### A. Opening restraint → middle expansion → late contraction
Strong examples:
- Waltz For Debby
- Autumn Leaves
- Blue In Green
- Peri's Scope
- B Minor Waltz
- Re: The Person I Knew

This is common, but must remain a prior rather than a fixed envelope.

### B. Opening restraint → middle expansion → late re-expansion
Examples:
- Alice In Wonderland
- You Must Believe In Spring, but less stable

This requires a narrative state capable of reopening intensity after a release.

### C. Stronger opening / middle contraction → late expansion
Examples:
- Nardis
- In Your Own Sweet Way
- Israel, probabilistically

This is the strongest warning against a universal Bill-Evans-trio arc.

### D. Late foreground allocation
`Without A Song` places the activity peak in the last 30% in 1000/1000 passes.
Combined with the known drum-solo allocation, this shows that a drummer may
remain supportive for a long span and later acquire foreground ownership.

## Implications for AI Drummer

### 1. Position is a prior, never an action
Normalized song position can help estimate expected narrative phase, but should
not directly choose density or fill behavior.

### 2. Need a role/narrative state above gesture selection
Immediate comping probability is too shallow. Repeated evidence supports a layer
that asks:
- who owns the foreground?
- who is carrying pulse clarity?
- is the current task support, transition, development, or release?
- has the drummer already contributed enough?
- is a late re-expansion musically justified?

### 3. Opening restraint is often role-rich
Low activity at the opening should not be interpreted as "do nothing."
It can mean:
- clear but light pulse
- brush/ride texture
- preserving melody sustain
- allowing bass independence
- delaying conversational entry

### 4. Terminal contraction is highly common but not universal
The last decile is below zero in 100% of album-level passes, yet individual
tracks can re-expand before the terminal drop.

Therefore ending logic needs at least:
- current narrative direction
- explicit ending/coda evidence
- role ownership
- distance to actual terminal boundary

### 5. Form knowledge and marking need remain separate
The 1000-pass result strengthens, rather than weakens, the previous conclusion:

**FORM KNOWLEDGE ≠ FORM MARKING**

Knowing the exact structural boundary does not imply a fill/crash.

### 6. Meter and pulse responsibility remain separate
The score-aligned examples still support:

**METER ≠ PULSE RESPONSIBILITY**

Head/solo role can change how the drummer clarifies pulse without changing the
notated meter.

## What should NOT be learned from this study

Do not learn:
- a fixed Bill Evans density envelope
- "always build in the middle"
- "always back off at the end"
- "Paul Motian = sparse"
- "Eliot Zigmund = active"
- a direct mapping from spectral brightness to cymbal strokes

The analysis is whole-mix and context-sensitive.

## Next evidence step

The next valuable step is no longer more generic whole-album passes.

It is **bar-aligned annotation** on a smaller set of high-information tracks:

1. Autumn Leaves
2. Waltz For Debby
3. Peri's Scope
4. Nardis
5. In Your Own Sweet Way
6. Without A Song

For each:
- align score bars / sections / navigation to audio
- mark head, solo, bass-solo, drum-solo, re-entry, coda where verified
- measure drum-surface change around those boundaries
- annotate whether the drummer's role changes even when energy does not
- compare repeated form positions across choruses

That is the point where signal evidence can become semantic drummer intelligence.
