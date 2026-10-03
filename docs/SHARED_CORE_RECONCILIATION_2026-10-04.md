# Shared Core reconciliation — 2026-10-04

Several workstreams landed overlapping implementations at nearly the same time.
This note fixes ownership so future branches converge instead of creating parallel
"canonical" systems.

## Canonical ownership after repository review

### Musical position

There is one persisted/shared canonical research coordinate:

`music_intelligence.learning.MusicalScoreCoordinate`

It already carries:
- song / score source identity
- `realchord_id`
- section
- bar / beat
- form bar / form length
- chorus
- performance phase
- harmonic/form/navigation context

Other position objects may exist as detector/runtime projections, but they must
adapt into `MusicalScoreCoordinate` before learning, cross-recording comparison,
or persistent Shared Core storage.

Do **not** introduce a second `CanonicalMusicalCoordinate`.

### RealChord

Canonical RealChord ownership is:

`music_intelligence.corpus.realchord`

RealChord supplies expected chart/form structure. It never overwrites performed
Observed or Inferred Harmony.

Stable identity comes from the normalized RealChord record. Runtime code must not
hard-code playlist source-order numbers such as "Autumn Leaves = 96" as a global
identity contract.

### Expressive intelligence

Canonical HOW ownership is:

`music_intelligence.expression`

This package already owns:
- relative expression profiles
- contextual expressive realization
- motif-expression memory
- post-commit HOW memory
- player solo-expression compatibility adapter

Do **not** add a second Shared engine under
`music_intelligence.reasoning.expressive_realization`.

Player/realtime branches should consume the Shared `ExpressiveIntent` and only
translate it into physical controls.

### Autonomous Research Listener

The Listener owns source selection, playback/capture/session state and research
orchestration. It must consume Shared:
- Audio Evidence
- Form/score alignment
- `MusicalScoreCoordinate`
- RealChord expected structure
- MusicalMoment / learning admission

A Listener-local metric/form object may be an intermediate estimate only; it is
not a second canonical learning address.

### Vocabulary

Existing Legend vocabularies and new general/shared vocabulary must use the same
`VocabularyMemoryItem` contract.

Project runtime policy is:
- approximately 30% direct/literal use when an admitted literal representation
  exists and literal use is allowed;
- approximately 70% transformed/adapted/fragment/abstract/hybrid use;
- no literal payload -> transformed fallback.

Direct reuse does not change the causal runtime rule: a stored phrase may be
known as a whole, while online performance still commits the current event and
listens again.

## Branch/PR consequences

- PR #59 duplicated Shared Expressive Intelligence that has since landed on
  `main` through PRs #60/#61. Preserve only its quartet/player wiring ideas.
- PR #63 duplicated RealChord/canonical-coordinate work that has since landed on
  `main` through PR #62 plus the form-first coordinate work from PR #57.
  Preserve only non-duplicative adapters after rebasing.
- PR #51 currently describes `MetricFormPosition` as canonical. Before merge,
  it must treat that representation as an intermediate form estimate and adapt
  to `MusicalScoreCoordinate`; its status text claiming no visible RealChord
  source is now stale.
- PRs #54-#58 were written before later Bill Evans / LaFaro vocabulary and
  form-relative research landed on `main`. Their assumptions about empty
  vocabulary stores must be rechecked before merge.

## Merge rule

When two workstreams implement the same musical concept, prefer:

1. the Shared Core implementation already merged to `main`;
2. adapters from workstream-specific representations into that Shared contract;
3. deletion/supersession of duplicate "canonical" types.

Do not merge two competing canonical representations and try to reconcile them
at runtime.
