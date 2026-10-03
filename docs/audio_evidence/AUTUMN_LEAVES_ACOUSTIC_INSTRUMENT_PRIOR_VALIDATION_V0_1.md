# Autumn Leaves Acoustic Instrument Prior Validation v0.1

This pass validates the conservative `AcousticInstrumentPriorDetector` on the
BE-003 Autumn Leaves segment.

The detector uses only pitch register and onset-local spectral centroid. It does
not use chord progression, form, phrase, ensemble role, score position, or
notation context.

## Mixture

From 7,240 spectral pitch hypotheses:

- top bass hypothesis: **2,133**
- top piano hypothesis: **5,107**
- margin < 0.15: **945 (13.05%)**
- low-register hypotheses (MIDI <= 52): **2,299**
- low-register margin < 0.15: **945 (41.10%)**
- low-register median top-vs-runner-up margin: **0.1514**

The detector therefore behaves as intended around the difficult low register:
a large portion remains explicitly ambiguous rather than being forced into Bass
or Piano ownership.

## HPSS harmonic stream

From 8,478 spectral pitch hypotheses:

- top bass hypothesis: **2,827**
- top piano hypothesis: **5,651**
- margin < 0.15: **941 (11.10%)**
- low-register hypotheses (MIDI <= 52): **2,857**
- low-register margin < 0.15: **941 (32.94%)**

Relative to the mixture, low-register ambiguity falls by about **8.17
percentage points**.

This is not evidence that HPSS correctly separated Bass from Piano. HPSS only
changes the acoustic representation. The result demonstrates that instrument
posterior quality is sensitive to the upstream representation and reinforces
the need to preserve separator provenance.

## Engine implication

The current baseline supports the following policy:

```text
strong acoustic distinction
    → instrument prior may become decisive

Bass/Piano-LH overlap
    → preserve alternatives
    → mark hard example
    → wait for stronger acoustic/separation/context evidence
```

No Core harmony/form/ensemble semantics were introduced to obtain these
numbers. This keeps the Audio Evidence / Music Intelligence Core boundary
intact.
