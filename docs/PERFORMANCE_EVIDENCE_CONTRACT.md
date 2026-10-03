# Performance Evidence Contract

## Ownership

The transcription workstream owns the common `Performance Evidence` intake contract in:

`src/music_intelligence/transcribe/events.py`

Audio Evidence may import or adapt to this contract, but must not own or clone it. Transcription consumes this contract and must not import detector-internal Audio Evidence schemas.

## Current version

`performance-evidence.v1`

The version identifies the compatibility surface expected by adapters. Additive fields may be introduced without changing the major version when existing consumers remain valid. Removing or renaming required fields, changing their meaning, or collapsing factorized evidence into a different semantic contract requires explicit compatibility review.

## Boundary

The contract represents committed or played performance evidence. It is not raw detector output, context-adjusted detector posterior, source-separation state, musical meaning owned by Core, score notation, or a LogicalScore event.

```
Audio Evidence internal schemas
        ↓ adapter
Performance Evidence
        ↓
Transcription Interpretation
        ↓
Notation Candidates
        ↓
LogicalScore
```

## Compatibility checks

`tests/contracts/performance_evidence_v1_expected.json` records the minimum field surface required by the current contract. CI compares it with the actual dataclasses so accidental removal or renaming becomes visible contract drift.

This fixture is a compatibility expectation, not a duplicate runtime schema.

## Canonical musical coordinate

Downstream musical reasoning MUST prefer `MusicalCoordinate` over absolute
seconds or transport position.  The canonical address is form/section/chorus/
bar/beat/subdivision, with confidence and explicit uncertainty for pickup,
meter-change, rubato/free-time, and through-composed material. Physical seconds
remain source evidence and alignment provenance.

## Perceptual dynamics

Each event may carry `PerceptualDynamics` in addition to the legacy scalar
`dynamic`. The factorized contract separates source-normalized perceptual
level from track/section/phrase-relative level and dynamic change. Evidence may
include calibrated level, brightness, attack, harmonic/noise balance, register,
ensemble density, articulation, sustain/body, and local musical context.
Mastered loudness alone must not be interpreted as musical absolute dynamics.
