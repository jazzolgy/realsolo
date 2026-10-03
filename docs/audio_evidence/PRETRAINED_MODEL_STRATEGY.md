# Pretrained Audio Models Strategy

The Audio Evidence Engine should prefer existing pretrained models where they
fit the evidence task, rather than training every stage from scratch.

## 1. Source separation

Primary baseline:
- Demucs `htdemucs`: drums / bass / other / vocals
- Demucs `htdemucs_6s`: drums / bass / other / vocals / guitar / piano

The six-stem model is particularly useful for the Jazz Trio validation path
because it exposes both bass and piano stems. Its piano stem is experimental,
so the separation output must remain probabilistic evidence rather than ground
truth.

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

## Commercial/licensing note

Model code and weight licenses must be checked separately before packaging.
A technically useful pretrained model is not automatically suitable for a
commercial distribution.
