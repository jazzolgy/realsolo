# BE-003 Autumn Leaves — note-by-note transcription layer v0.1

Date: 2026-10-03
Source: owner-supplied `be_playlist_project_audio`
Track window: 708.0–1069.0 s (11:48–17:49)
Training-rights disposition: DERIVED_ONLY / OBSERVATION_ONLY
Publication default: PUBLIC_DERIVED

## Purpose

Priority has shifted from broad robustness scanning to a note/event transcription
layer for Autumn Leaves, followed by Piano / Bass / Drums interaction analysis.

Detailed derived analysis is now preserved in the public repository by default.
`DERIVED_ONLY` controls training admission; it does not imply that analysis
artifacts must remain private.

The source audio itself and source-derived full stems are not committed.

## Event layer generated

### Harmonic / pitched layer

- 2,000 harmonic onsets detected
- 9,742 pitch hypotheses attached to those onsets
- each event representation is designed to store:
  - relative/source timestamp
  - estimated beat index
  - estimated 4/4 bar/beat position
  - pitch MIDI / note name
  - estimated sounding duration
  - spectral confidence
  - instrument/source probabilities
  - polyphony-at-onset
  - harmony / score-position evidence
  - revision history
  - `NOTE_HYPOTHESIS` or later revision status

Initial register/source hypotheses:

- low register, bass-or-piano-low: 3,698
- piano-LH-or-bass-high overlap region: 1,946
- piano-mid candidate: 1,997
- piano-RH candidate: 2,101

These are not final instrument assignments. Mixed trio audio creates substantial
Piano-LH/Bass ambiguity in overlapping registers.

### Percussive layer

- 1,311 percussive onsets detected
- event representation is designed to store:
  - timestamp
  - beat/bar estimate
  - low/mid/high spectral-energy ratios
  - drum-class probabilities
  - class confidence
  - revision history
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
worth targeted verification because it may reflect phrase-lift / setup behavior,
but it can also be caused by shared mix-energy changes. It must be checked
against score/form position and stronger instrument attribution before becoming
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

## Publication rule for future passes

Future event-level derived artifacts should be committed rather than collapsed
to aggregate summaries when the artifact is useful for engine development and
does not embed the source audio or a source-equivalent score/facsimile.

This includes:
- event IDs and timestamps;
- pitch hypotheses;
- instrument probabilities;
- role probabilities;
- factorized confidence;
- score-position hypotheses;
- attribution revisions;
- hard-example labels;
- phrase/gesture grouping;
- interaction events.

If a particular export becomes a practical full-score or source substitute, that
specific payload is REVIEW_REQUIRED; the rest of the analysis remains public.

## Next verification pass

1. align the beat grid to the visually verified Autumn Leaves score;
2. identify canonical form and chorus boundaries;
3. mark Head / Solo / Out-Head / Ending with probabilities rather than forced labels;
4. reassign each low-register hypothesis between Bass and Piano LH using:
   - continuity,
   - spectral envelope,
   - register trajectory,
   - simultaneous piano chord evidence,
   - score/harmony position;
5. refine Piano RH/LH grouping into gesture/chord/line events;
6. refine drum events into ride / hi-hat / snare / kick / cymbal/setup classes;
7. compare interaction around phrase boundaries and repeated harmonic locations;
8. preserve revisions and failed hypotheses as engine-development data;
9. only then promote repeated evidence into Bill Evans or Shared Ensemble tendencies.

## Promotion boundary

SOURCE
-> NOTE/EVENT HYPOTHESIS
-> INSTRUMENT ATTRIBUTION
-> SCORE/BAR/CHORUS ALIGNMENT
-> PHRASE/GESTURE GROUPING
-> INTERACTION EVIDENCE
-> REPEATED EVIDENCE
-> BILL EVANS CONDITIONAL TENDENCY
-> possible SHARED TRIO/ENSEMBLE GRAMMAR

Public analysis visibility does not update training priors. Training permission
remains an independent rights gate.
