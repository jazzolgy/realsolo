# Current-main runtime reconciliation — 2026-10-04

This change reconnects the useful ideas from open workstreams #51 and #53–#56
to the contracts that are now canonical on `main`. It intentionally does not
merge their duplicate Shared-Core types.

## Canonical ownership

- musical position: `music_intelligence.learning.MusicalScoreCoordinate`
- RealChord / Expected Harmony: `music_intelligence.corpus.realchord`
- HOW: `music_intelligence.expression`
- Audio Evidence implementation: `music_intelligence.learning.audio_evidence`
- public Audio Evidence import facade: `music_intelligence.audio_evidence`
- vocabulary ranking/reuse: `music_intelligence.vocabulary`

The top-level Audio Evidence module is only a re-export. It contains no second
engine.

## #51 Autonomous Listener

A Listener detector may retain its transient metric/form estimate while
listening. Before persistence, comparison, or learning it must call:

`coordinate_from_listener_estimate(...)`

That adapter returns `MusicalScoreCoordinate`. Seconds remain audio provenance
outside the coordinate.

So the ownership boundary is:

```
listener/detector form estimate
        ↓ adapter
MusicalScoreCoordinate
        ↓
learning / comparison / RealChord / expression
```

## #53–#56 runtime stack

The old stacked runtime branches should consume
`build_canonical_runtime_context(...)` rather than recreating Shared concepts.

The bridge combines, for one immediate decision only:

```
MusicalScoreCoordinate       WHEN
RealChord Expected Harmony   harmonic reference
Expression engine            HOW
Legend Vocabulary            optional WHAT prior
```

It does not schedule an exact future phrase.

## Legend state correction

Profile and Vocabulary availability are separate.

Current `main` behavior is explicitly test-covered:

- Bill Evans: profile tendencies unavailable; source-grounded vocabulary
  available.
- Charlie Parker: profile tendencies available; public vocabulary index empty.
- Scott LaFaro: profile and source-grounded abstract vocabulary are available.

Therefore a runtime must never infer “no vocabulary” from an empty
`LegendProfileView`.

## Vocabulary reuse

The existing `music_intelligence.vocabulary.usage_policy` now owns the
reproducible direct/transformed selection rule:

- nominal 3-of-10 opportunities may be literal when a literal payload exists
  and literal use is allowed;
- all other opportunities prefer hybrid / abstract / fragment / adapted /
  transposed use;
- if literal data does not exist, a direct slot automatically falls back to a
  transformed use.

This is a listening/evaluation target, not a requirement that every phrase be
30 percent quoted material.

## Migration consequence

Do not merge the old branches by reintroducing:

- `CanonicalMusicalCoordinate`
- a second expressive-realization engine
- a second audio-evidence engine
- a runtime-local Legend/Vocabulary truth store

Port their remaining UI, playback, scheduling, and audible quartet code as
consumers of the adapters above.


## Integration work branch

`integration/canonical-listening-runtime-20261004` is the fixed selective-port branch. At the initial 2026-10-04 preflight it was identical to main `762fa05c243867ec9afbc1a5fe3cbcfed7b7d41e`. Runtime work must re-check main before each write and avoid parallel Shared-Core owners.
