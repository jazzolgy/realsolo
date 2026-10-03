# BE-003 Autumn Leaves — note-by-note transcription layer v0.1

Date: 2026-10-03
Source: owner-supplied `be_playlist_project_audio`
Track window: 708.0–1069.0 s (11:48–17:49)
Disposition: DERIVED_ONLY / OBSERVATION_ONLY

## Purpose

Priority has shifted from broad robustness scanning to a note/event transcription
layer for Autumn Leaves, followed by Bill Evans / Bass / Drums interaction analysis.

The exact event stream is kept private/local because a complete note-by-note
transcription of copyrighted audio is reconstructive. This public research note
stores only schema, counts, confidence rules, and non-reconstructive aggregates.

## Private event layer generated

### Harmonic / pitched layer

- 2,000 harmonic onsets detected
- 9,742 pitch hypotheses attached to those onsets
- each event stores:
  - relative/source timestamp
  - estimated beat index
  - estimated 4/4 bar/beat position
  - pitch MIDI / note name
  - estimated sounding duration
  - spectral confidence
  - source hypothesis
  - source confidence
  - polyphony-at-onset
  - `NOTE_HYPOTHESIS` status

Initial register/source hypotheses:

- low register, bass-or-piano-low: 3,698
- piano-LH-or-bass-high overlap region: 1,946
- piano-mid candidate: 1,997
- piano-RH candidate: 2,101

These are not final instrument assignments. Mixed trio audio creates substantial
Piano-LH/Bass ambiguity in overlapping registers.

### Percussive layer

- 1,311 percussive onsets detected
- event schema stores:
  - timestamp
  - beat/bar estimate
  - low/mid/high spectral-energy ratios
  - drum-class hypothesis
  - class confidence
  - `EVENT_HYPOTHESIS` status

Initial class hypotheses:

- snare-or-mid-percussion: 1,143
- kick-or-low-percussion: 85
- cymbal-or-hi-hat: 22
- unresolved percussive event: 61

These labels are intentionally conservative and require stronger drum-specific
verification before promotion.

## Timing layer

- pulse estimate: 103.36 BPM
- beat positions detected: 608
- rough 4/4 bar-equivalent count: 152

The bar numbers are audio-grid estimates only. They are not yet canonical score
bar numbers or chorus positions.

## First interaction evidence from the note/event layer

Using the provisional register/instrument hypotheses by estimated bar:

- low-register activity vs RH-candidate activity correlation: about -0.03
- RH-candidate activity vs same-bar drum activity correlation: about +0.52
- low-register activity vs same-bar drum activity correlation: about +0.16
- RH-candidate activity vs next-bar drum activity correlation: about +0.28

Interpretation status: navigation evidence only.

The stronger RH/drum co-activity compared with low-register/drum co-activity is
worth targeted listening because it may reflect phrase-lift / setup behavior,
but it can also be caused by shared mix-energy changes. It must be verified
against score/form position and instrument-separated listening before becoming
an ensemble-interaction claim.

## High-value provisional audio-grid locations

Examples selected for the next verification pass:

- bar-est. 46 (~13:32.8 source): unusually low-register-dominant event balance
- bar-est. 70–71 (~14:28.4–14:30.6): strong RH-candidate activity
- bar-est. 91–93 (~15:16.6–15:21.2): high ensemble activity / low-register weight
- bar-est. 104 (~15:46.8): RH-heavy candidate
- bar-est. 128 (~16:41.9): sparse/release candidate
- bar-est. 139–143 (~17:07.3–17:16.8): high late-form activity, including RH/drum co-activity
- bar-est. 147 (~17:26.3): sparse/release candidate
- bar-est. 152 (~17:37.8): final-zone candidate

These bar estimates are deliberately not labeled Head/Solo/Out-Head yet.

## Next verification pass

1. align the beat grid to the visually verified Autumn Leaves score;
2. identify canonical form and chorus boundaries;
3. mark Head / Solo / Out-Head / Ending;
4. reassign each low-register hypothesis between Bass and Piano LH using:
   - continuity,
   - spectral envelope,
   - register trajectory,
   - simultaneous piano chord evidence,
   - score/harmony position;
5. refine Piano RH/LH grouping into gesture/chord/line events;
6. refine drum events into ride / hi-hat / snare / kick / cymbal/setup classes;
7. compare interaction around phrase boundaries and repeated harmonic locations;
8. only then promote repeated evidence into Bill Evans or Shared Ensemble tendencies.

## Promotion boundary

SOURCE
-> NOTE/EVENT HYPOTHESIS
-> INSTRUMENT ASSIGNMENT
-> SCORE/BAR/CHORUS ALIGNMENT
-> PHRASE/GESTURE GROUPING
-> INTERACTION EVIDENCE
-> REPEATED EVIDENCE
-> BILL EVANS CONDITIONAL TENDENCY
-> possible SHARED TRIO/ENSEMBLE GRAMMAR

No exact note stream is committed publicly, and no derived observation updates
training priors without explicit training permission.
