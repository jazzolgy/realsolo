# Architecture Boundary Guard

This guard exists because Audio Evidence, Music Intelligence Core, and
AI Transcription + Notation are developed in parallel.

The guard turns architectural boundaries into repository checks rather than
relying on memory alone.

## Canonical boundary

```text
Audio / MIDI
    ↓
Audio Evidence Engine
    ↓
Performance Evidence
    ↓
Music Intelligence Core
    ↓
Transcription / Ensemble / Learning / Player
```

These stages remain distinct:

```text
raw detector output
≠ context-adjusted posterior
≠ committed Performance Evidence
≠ musical meaning
≠ notation
```

## Enforcement

`docs/ARCHITECTURE_OWNERSHIP.toml` is the machine-readable ownership source.

`tests/architecture/test_architecture_boundaries.py` enforces:

- Audio Evidence may not import Transcription, Learning, or Core semantic modules directly.
- Transcription may not import Audio Evidence internals.
- Audio Evidence may not grow duplicate semantic modules such as harmony, form,
  phrase, ensemble, notation, engraving, MusicXML, or LogicalScore.
- declared owned roots must remain non-overlapping.
- when the Performance Evidence contract exists in a branch, its version and
  observation/posterior fields must match the declared contract snapshot.

The contract check is intentionally future-aware: branches that do not yet
contain `music_intelligence.transcribe.events` skip only that contract-specific
check. Once the contract is present, drift becomes a test failure.

## Required development preflight

Before a substantive batch in any workstream:

1. read latest `main` head;
2. read the relevant sibling workstream heads;
3. inspect Performance Evidence contract version if present;
4. check for overlapping files or ownership changes;
5. develop only inside the declared ownership boundary;
6. run the architecture tests before opening/updating a PR.

If a workstream needs another workstream's contract changed, it should submit a
contract requirement rather than editing the foreign-owned implementation.
