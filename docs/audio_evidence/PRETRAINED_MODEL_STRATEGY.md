# Pretrained Audio Models Strategy

The Audio Evidence Engine should prefer existing pretrained models where they
fit the evidence task, rather than training every stage from scratch.

## 1. Source separation

Primary research baseline:

- Demucs `htdemucs`: drums / bass / other / vocals
- Demucs `htdemucs_6s`: drums / bass / other / vocals / guitar / piano

The six-stem model is the most directly useful pretrained separator for the
Jazz Trio validation path because it exposes both bass and piano stems. The
upstream project describes the piano source as experimental and reports
bleeding/artifacts, so the output remains probabilistic acoustic evidence.

A second pretrained fallback is available through TorchAudio:

- `HDEMUCS_HIGH_MUSDB`
- `HDEMUCS_HIGH_MUSDB_PLUS`

These are four-stem Hybrid Demucs bundles: drums / bass / other / vocals.
They are useful for isolating bass and drums, but piano remains in `other`.

The repository adapters are:

```text
DemucsCLISeparator
TorchAudioHDemucsSeparator
LibrosaHPSSSeparator   # validation fallback, not an instrument separator
```

## 2. Generic instrument tagging

AudioSet-family pretrained taggers such as YAMNet can provide coarse frame-level
evidence for labels including piano, double bass/bass guitar, percussion, drum
kit, snare drum, bass drum, cymbal, and hi-hat.

These models are not note-level ownership systems. The engine therefore maps
their frame scores to a deliberately weak `AudioSetInstrumentPriorDetector`
instead of committing note ownership directly.

## 3. Note-level instrument attribution

The engine exposes:

- `InstrumentFeatureEncoder`
- `InstrumentProbabilityBackend`
- `LearnedInstrumentClassifier`
- optional `TorchScriptInstrumentBackend`

This lets a future jazz-specific classifier be added without changing the
detector, posterior, Performance Evidence, or Transcription contracts.

The current detector-side feature baseline includes pitch/frequency and
onset-local spectral centroid, flatness, rolloff, RMS, and zero-crossing rate.

## 4. Availability is not validation

Pretrained model presence must be tracked separately from adapter availability.

```text
adapter implemented
!= pretrained weights available
!= inference executed
!= quality validated
!= production approved
```

In the current execution environment Demucs and Torch are installed, but the
`htdemucs_6s` checkpoint is not cached and direct model-weight download is not
available from the analysis runtime. Therefore the code path is implemented and
unit-testable, while BE-003 six-stem quality remains unclaimed until a checkpoint
is available.

## 5. Deployment review

Code licensing, model-weight licensing, training-data terms, and commercial
deployment suitability are separate questions.

The engine records `deployment_review_required` in its pretrained-model
registry instead of assuming that an open-source implementation automatically
grants production rights for its weights.

## Validation policy

Pretrained model output is always evidence:

```text
pretrained separator/tagger output
!= ground truth
!= committed Performance Evidence
!= musical meaning
```

For Bass-vs-Piano-LH, model comparison should report coverage, ambiguity rate,
top-label disagreement, and calibrated confidence before any model is promoted
to production use.
