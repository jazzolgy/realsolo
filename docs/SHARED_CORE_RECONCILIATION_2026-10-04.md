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


## Additional concurrent-branch collision matrix

Repository-wide review found several older/open branches that should not be
merged independently without reconciliation.

| Area | Branches / PRs | Coordination decision |
| --- | --- | --- |
| Audio evidence | #27 Shared Audio Intelligence, #39 Audio Evidence Engine | #39 is the canonical engine direction. Preserve unique public-safe research artifacts/bridge ideas from #27, but do not keep a second `audio_intelligence` engine namespace. |
| Transcription / notation | #7 versus #29–#32 | They edit the same `transcribe` contracts and implementation files. #29–#32 define the newer Performance Evidence / Notation boundary; #7's richer product features should be ported onto those contracts rather than merged as an alternative engine. |
| Groove/realtime | #26 and #45+ | Current `main` already contains Shared `GrooveTemporalContext`, role timing profiles, and coordination modes. Realtime branches must consume that module and must not replace it with branch-local variants. |
| Decision observability | #40/#43/#44 | These are complementary when stacked in order: DecisionContextLog → Player audit hooks → MusicalMoment. Keep observability descriptive; no reward/causal attribution. |
| Autonomous research form state | #51 versus #57/#62 on main | Listener-local form estimates may remain, but persistent/cross-source identity must adapt to `MusicalScoreCoordinate` and RealChord expected structure. |
| Legend/vocabulary/runtime | #54–#56 | Recheck assumptions against current main: Bill Evans profile remains empty, but Bill Evans/LaFaro vocabulary stores now contain source-grounded items. |

### Transcription integration rule

Do not maintain two parallel event/notation models. Use the newer standalone
boundary as the contract, then port mature #7 capabilities (dynamics, chord
chart, instrument rules, piano handling, engraving, product views) behind that
contract.

### Audio integration rule

`music_intelligence.audio_evidence` is the canonical detector/posterior engine
namespace. Any useful #27 artifacts should enter as:
- research/validation artifacts,
- adapters,
- schemas compatible with Audio Evidence,
- or test fixtures.

They should not preserve a second top-level Shared Audio engine with overlapping
posterior/revision ownership.
