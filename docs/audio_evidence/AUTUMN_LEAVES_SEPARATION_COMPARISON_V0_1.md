# Autumn Leaves Separation Comparison v0.1

This pass compares the direct mixture baseline with a real HPSS separation run
on the owner-provided BE-003 Autumn Leaves segment.

The goal is not to claim that HPSS solves instrument ownership. The goal is to
validate the Audio Evidence Engine separation boundary and measure how detector
outputs change when the acoustic stream changes.

## Direct mixture baseline

- onset hypotheses: **1,421**
- spectral pitch hypotheses: **7,240**
- mean pitch hypotheses/onset: **5.095**
- unpitched hypotheses: **1,398**
- weak token split: kick 11 / snare 1,237 / cymbal-or-hihat 150

## HPSS harmonic stream

- onset hypotheses: **1,796**
- spectral pitch hypotheses: **8,478**
- mean pitch hypotheses/onset: **4.720**
- RMS: **0.06317**

The harmonic stream produces more detected onsets and more pitch hypotheses
than the direct mixture. This is useful evidence that detector output is not an
absolute property of the performance; it depends on the upstream acoustic
representation and must retain separator provenance.

## HPSS percussive stream

- onset hypotheses: **1,691**
- weak token split: kick 13 / snare 1,466 / cymbal-or-hihat 212
- RMS: **0.02659**

The high-frequency token count rises relative to the direct mixture. The labels
remain weak spectral classes rather than confirmed drum identities.

## Demucs status

The `DemucsCLISeparator` adapter and its unit tests are implemented. A real
`htdemucs` run was attempted on the materialized 361-second BE-003 segment,
but the execution environment did not contain the model weights and could not
download them. No Demucs quality result is therefore claimed.

This distinction is intentional:

```text
adapter implemented
≠ model weights available
≠ separation executed
≠ separation quality validated
```

## Architectural conclusion

HPSS is sufficient to validate:

```text
materialized source
→ separator
→ SeparatedSource
→ separation metadata
→ detector chain
→ AudioObservation
→ posterior
```

It is **not** sufficient for the central Bass-vs-Piano-LH attribution problem.
That problem remains for a learned multi-stem separator and/or dedicated
instrument attribution evidence.

No harmony, form, phrase, ensemble meaning, or notation was inferred in this
comparison.
