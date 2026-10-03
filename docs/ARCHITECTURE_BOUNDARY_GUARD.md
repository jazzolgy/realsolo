# Architecture Boundary Guard

The repository checks subsystem boundaries in code so parallel development does not rely only on memory.

## Ownership policy

`docs/ARCHITECTURE_OWNERSHIP.yaml` defines subsystem paths, allowed contract access, dependency restrictions, the Performance Evidence contract location/version, and the development workflow.

It uses JSON-compatible YAML so the checks can read it with the Python standard library.

## Workflow

```text
Architecture Preflight
→ Development
→ Boundary Audit
→ Tests
→ Pull Request
```

Example:

```text
python scripts/architecture_preflight.py --area audio_evidence --base origin/main
```

The preflight compares changed files with the selected area's ownership rules.

## CI checks

`tests/architecture/` checks imports using Python AST inspection. It keeps Audio Evidence separate from notation internals, keeps Transcription separate from detector internals, and keeps Shared Core separate from Player implementations.

GitHub Actions runs the architecture checks on every pull request before the full test suite.

## Performance Evidence compatibility

`tests/contracts/performance_evidence_v1_expected.json` stores a minimum compatibility snapshot: contract version, public types, and required event fields. Additive fields are allowed. Required type or field removal is reported as contract drift.

The intended relationship is:

```text
Audio Evidence → Performance Evidence → Core / Transcription
```

Audio Evidence can consume the shared contract through its adapter boundary, while its detector/posterior internals remain private. Transcription consumes Performance Evidence rather than Audio Evidence internals. Shared Core owns musical meaning and instrument-neutral reasoning.

## Parallel development

Before each development batch, check the current base, Performance Evidence version, and changed-file overlap. If the shared contract changed, verify adapter compatibility first rather than copying the contract into subsystem-internal schemas.
