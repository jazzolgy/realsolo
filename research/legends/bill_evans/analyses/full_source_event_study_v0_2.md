# Bill Evans Full-Source Event Study v0.2

Date: 2026-10-03

## Scope

Two project-owner supplied Bill Evans compilations were analyzed end to end:

- be_best_full_album_project_audio — 3760.054 s
- be_playlist_project_audio — 7717.956 s

Total source duration analyzed: 11478.010 s (3 h 11 m 18 s).

This pass is event-level and exhaustive across the available audio, but it is
not claimed as ground-truth note transcription. Both files are mixed recordings,
so automatic pitch events remain NOTE_HYPOTHESIS / OBSERVATION_ONLY until
instrument separation, score/form alignment, or expert listening confirms them.

## Analysis pass

Private/local processing used:

1. mono conversion at 8 kHz;
2. 1024-point STFT, 256-sample hop;
3. spectral-flux onset detection;
4. tonal spectral-peak extraction at each onset;
5. up to four pitch hypotheses per onset;
6. confidence score per pitch hypothesis;
7. 5-second aggregate windows for onset density, RMS and pitch-class profile.

The exact per-event JSONL is intentionally not committed to the public
repository because it is derived from copyrighted/private audio and can be too
reconstructive. Only non-reconstructive aggregate evidence is committed.

## Event totals

- Best Full Album: 13,872 detected onsets; 52,619 pitch hypotheses.
- Project playlist: 26,758 detected onsets; 97,547 pitch hypotheses.
- Combined: 40,630 detected onsets; 150,166 pitch hypotheses.

These counts are analytical hypotheses, not claims about the true number of
performed notes.

## Learning-system change

The SharedLearningEngine now separates:

- training priors — only artifacts with explicit training permission;
- evidence priors — derived research observations admitted for study even when
  training rights are unknown.

This lets RealSolo study the supplied recordings without silently converting
research/reference audio into training-authorized material.

The compact aggregate is converted into LearningArtifact objects for:

- RHYTHM_GROOVE
- EXPRESSION
- VOCABULARY

and may be ingested with learn=False, study_as_evidence=True.

## Promotion rule

Nothing in this pass is automatically a Bill Evans runtime prior.

Promotion remains:

SOURCE
-> NOTE / EVENT HYPOTHESIS
-> SCORE / FORM / ROLE ALIGNMENT
-> REPEATED EVIDENCE
-> VOCABULARY / ABSTRACTION
-> CONDITIONAL LEGEND PRIOR

The next high-value pass is to take the event hypotheses into score-aligned
tracks (starting with Autumn Leaves) and assign piano RH/LH, bass and drums
roles by chorus/bar. That is where note-level evidence becomes musically useful
rather than merely acoustically dense.
