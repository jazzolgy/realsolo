# BE-003 Autumn Leaves — 100-pass deep navigation scan v0.1

Date: 2026-10-03
Source: owner-supplied `be_playlist_project_audio`
Track window: 708.0–1069.0 s (11:48–17:49)
Disposition: DERIVED_ONLY / OBSERVATION_ONLY

## Scope

This is a second-stage 100-pass scan of the isolated 361 s Autumn Leaves track.
It is intentionally narrower and deeper than the compilation-level 100/1000-pass
robustness studies.

100 passes = 10 analysis families × 10 smoothing/parameter settings.

The purpose is to identify **stable candidate transition / role-change windows**
for subsequent score/form and instrument-role verification. These are not
ground-truth chorus boundaries and not Bill Evans runtime priors.

## Analysis families

1. attack-density / spectral-flux activity
2. macro dynamic change
3. low-frequency presence
4. spectral-balance shift
5. timbre/centroid change
6. harmonic/chroma change proxy
7. multivariate ensemble-change proxy
8. sustain/body proxy
9. release/space proxy
10. broad spectral/dynamic contrast

Private/local analysis used mono 22.05 kHz audio, 2048-sample FFT windows,
512-sample hops, 5 s aggregate windows and ten robustness settings per family.
No reconstructive note stream is committed.

## Robust candidate windows

After excluding track-edge artefacts, the windows receiving the strongest
cross-family votes were:

| Relative track time | Source time | Cross-family vote | Interpretation status |
| --- | --- | ---: | --- |
| 350–355 s | 17:38–17:43 | 61 | very strong ending/release candidate |
| 345–350 s | 17:33–17:38 | 41 | strong pre-ending transition candidate |
| 245–250 s | 15:53–15:58 | 27 | strong internal change candidate |
| 340–345 s | 17:28–17:33 | 24 | late-form transition candidate |
| 45–50 s | 12:33–12:38 | 21 | early structural/role-change candidate |
| 250–255 s | 15:58–16:03 | 20 | continuation of internal change zone |
| 150–155 s | 14:18–14:23 | 20 | mid-track change candidate |
| 55–60 s | 12:43–12:48 | 20 | early-form contrast candidate |
| 155–160 s | 14:23–14:28 | 19 | continuation of mid-track change zone |
| 295–305 s | 16:43–16:53 | 31 combined across adjacent windows | late-middle change candidate |

The vote count is not musical confidence. It means that the same 5 s window
remained salient under many different feature families/settings.

## High-value grouped zones for the next listening/alignment pass

The 100 scans suggest five stable regions to inspect first:

- **45–60 s (12:33–12:48 source)** — early transition/role-change candidate
- **150–160 s (14:18–14:28 source)** — mid-track contrast candidate
- **245–260 s (15:53–16:08 source)** — strongest non-ending internal change zone
- **295–305 s (16:43–16:53 source)** — late-middle transition candidate
- **335–355 s (17:23–17:43 source)** — strong late-form/ending development zone

These windows should be checked against the visually verified Autumn Leaves
score pages before assigning head/solo/out-head labels.

## Musical questions for the score-aligned pass

At each zone annotate separately:

### Piano RH
- melody / variation / solo foreground / response / punctuation / space
- register trajectory
- phrase entrance/ending
- density and motif recurrence

### Piano LH
- voicing / punctuation / pulse support / bass complement / space
- register overlap with bass
- voicing body and release

### Bass
- time floor vs melodic foreground
- approach/connection family
- register and note-body trajectory
- repeated identity vs directional line
- lock vs independence from piano/drums

### Drums
- pulse maintenance
- setup / fill / phrase response
- density lift/reduction
- section cue / release

### Shared ensemble
- foreground/background handoff
- response delay
- density complementarity
- tension/release trajectory
- same-harmony/different-chorus realization differences

## Promotion rule

No window in this scan is promoted directly to Bill Evans Intelligence.

Promotion remains:

SOURCE
-> EVENT HYPOTHESIS
-> ROBUST NAVIGATION WINDOW
-> SCORE / FORM ALIGNMENT
-> INSTRUMENT / ROLE VERIFICATION
-> REPEATED EVIDENCE
-> BILL EVANS TENDENCY
-> CONDITIONAL LEGEND PRIOR

Only behavior that also recurs beyond Bill Evans evidence may be proposed for
Shared Trio / Ensemble Grammar.
