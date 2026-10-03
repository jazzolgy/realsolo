# BE-003 Autumn Leaves alignment checkpoint v0.3

Date: 2026-10-03
Source: owner-supplied `be_playlist_project_audio`
Track window: 708.0–1069.0 s (11:48–17:49)
Disposition: DERIVED_ONLY / OBSERVATION_ONLY

## Repo / contract check

- `main` HEAD re-checked before this pass.
- Bill Evans evidence remains owned by `research/legends/bill_evans/`.
- Shared Learning keeps evidence priors separate from rights-gated training priors.
- Piano remains realization-only; no private Bill Evans profile is created inside `players/piano/`.

## Important timing correction

The previous provisional beat layer used approximately 103.36 BPM and therefore
produced only about 150 four-beat bar-equivalents across the 361 s track.

A new tempogram / beat-tracking pass found a strong competing pulse near double
that rate:

- strongest slow pulse candidate: about 103.36 BPM
- strong double-tempo region: approximately 198–215 BPM
- forced 206.72 BPM tracking: 1,223 beat positions
- resulting four-beat bar candidates: about 305–306

This strongly suggests that the earlier ~103 BPM layer may be tracking a
half-time pulse rather than quarter-note jazz time.

Therefore all prior `bar_est` values remain navigation coordinates only and
must not be treated as canonical musical bars.

## 32-bar periodicity re-test

Using beat-synchronous chroma on the double-tempo grid, four possible bar phases
were tested.

Across all four phases, self-similarity at a 32-bar lag remained high:

- phase 0: mean 0.857, median 0.878
- phase 1: mean 0.855, median 0.875
- phase 2: mean 0.850, median 0.869
- phase 3: mean 0.847, median 0.868

For comparison, 16-bar lag similarity was slightly lower in the same analysis.

This is materially different from the earlier activity-count lag test. The
earlier test compared coarse event-density channels on a likely half-time grid;
the present test compares harmonic/chroma similarity on a double-tempo grid.

Interpretation:

- the evidence now supports a real 32-bar cyclic structure candidate;
- it still does **not** identify exact chorus boundaries or Head/Solo/Out-Head
  labels by itself.

## Score-template probe

A provisional 32-position chord-template sequence derived from the visually
verified project lead sheet was compared against the double-tempo bar chroma.

The best global template score remained only moderate (mean cosine similarity
about 0.586), and different 32-bar blocks preferred different score offsets.

This is expected under:

- improvisational reharmonization;
- bass/piano spectral overlap;
- chord extensions/substitutions;
- uncertain downbeat phase;
- mixed-audio chroma contamination.

Therefore no single global score offset is promoted yet.

## Consequence for the next pass

The alignment strategy is revised to:

1. retain the ~200 BPM quarter-note grid as the leading timing hypothesis;
2. use 32-bar harmonic self-similarity to locate candidate cycle boundaries;
3. estimate downbeat phase locally rather than globally;
4. use score harmony as a probabilistic emission, not a hard template;
5. compare repeated harmonic positions across candidate cycles;
6. only after stable alignment, revisit Piano-LH/Bass attribution and RH/Drums
   interaction windows.

The earlier provisional bars 22 / 46 / 91 / 93 and 70–71 / 139 / 142–145
remain useful audio-navigation anchors, but their musical bar numbers must be
recomputed on the corrected timing grid.

## Promotion boundary

No Head / Solo / Out-Head labels, exact chorus boundaries, exact instrument
ownership, or Bill Evans interaction tendency is promoted in this checkpoint.

The next milestone is a credible quarter-note/downbeat grid with probabilistic
32-bar cycle segmentation and uncertainty.
