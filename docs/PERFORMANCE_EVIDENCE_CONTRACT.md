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