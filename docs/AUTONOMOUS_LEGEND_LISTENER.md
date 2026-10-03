# Autonomous Legend Research Listener v0.1

## Goal

Build a semi-autonomous research listener that can:

1. discover candidate performances through an approved search provider,
2. rank candidates against current research gaps,
3. load a normal visible embedded player,
4. accept user-authorized system/tab audio capture,
5. stream compact acoustic evidence into Shared Audio Intelligence,
6. preserve raw detector evidence separately from context-corrected posteriors,
7. store non-reconstructive research artifacts and coverage metadata,
8. continue through a research queue while the local machine remains awake.

This design does **not** download or extract YouTube media files, bypass DRM, hide the
player, or treat embedded playback as an audio API.

## Architectural boundary

```text
Search provider
   -> ResearchSourceCandidate
   -> eligibility + ranking
   -> visible embedded playback
   -> user-authorized audio capture
   -> PCM frames
   -> realtime AudioFeatureExtractor
   -> Performance Evidence
      - raw detector output
      - context-corrected posterior
      - provenance
   -> MusicalMoment / StructuralPerformanceEvent
   -> Shared Learning / Legend research store
   -> coverage update
   -> next candidate
```

The player and capture path are intentionally separate. The embedded player controls
normal playback; capture is supplied by the browser/OS only after explicit user
permission.

## 24-hour operation

The research queue may be long-running, but v0.1 must not assume uninterrupted
24-hour playback. A run can pause for:

- browser or OS capture permission loss,
- computer sleep,
- network interruption,
- provider playback errors,
- autoplay/user-gesture requirements,
- unavailable/removed videos,
- ads or unexpected non-performance material,
- source eligibility changes.

The queue therefore uses resumable per-source states rather than treating the whole
night as one opaque session.

## Storage policy

Keep these distinct:

- source metadata and provenance,
- low-level/non-reconstructive acoustic features needed for later reasoning,
- raw detector probabilities,
- context-corrected probabilities,
- derived MusicalMoment / StructuralPerformanceEvent records,
- aggregate research artifacts,
- coverage information describing what remains underrepresented.

Do not persist source media bytes merely to make later re-analysis convenient. If a
future detector requires evidence that was not retained, mark that field unknown
rather than inventing a value.

## Research source states

```text
DISCOVERED
 -> ELIGIBLE
 -> QUEUED
 -> PLAYING
 -> ANALYZING
 -> COMPLETE

Any stage may also become:
SKIPPED / BLOCKED / FAILED / PAUSED
```

## Candidate ranking

The rank is research-oriented rather than popularity-oriented. Initial factors:

- identity confidence for artist/personnel,
- source reliability,
- embeddable/playable status,
- audio suitability,
- duration suitability,
- research coverage gap,
- duplicate/performance-family penalty,
- recent-use penalty.

No single source should dominate a LegendProfile merely because it has many uploads.

## First implementation target

v0.1 only defines the queue/policy contract. Follow-up work should connect it to:

- provider search adapter,
- Stage1/Research web UI,
- getDisplayMedia/tab-audio capture,
- streaming PCM endpoint,
- Shared Audio Intelligence evidence ingestion,
- resumable research manifest.


## Open-set instrument discovery

The research listener must not assume that the permanent RealSolo instrument set is
piano/bass/drums/saxophone. Instrument recognition is open-set.

When an unsupported instrument is heard, keep its detector distribution and role
evidence rather than forcing it into the nearest supported class. Repeated evidence
across multiple sources can promote it to an `InstrumentProfileCandidate`.

Promotion criteria are conservative by default:

- evidence from multiple distinct sources,
- repeated occurrences,
- enough accumulated audible duration,
- sufficiently high mean confidence,
- retained role probabilities and family evidence.

Example:

```text
unknown / trombone candidate
    -> source A evidence
    -> source B evidence
    -> source C evidence
    -> promotion threshold met
    -> InstrumentProfileCandidate(trombone, brass)
    -> research profile begins accumulating
```

Promotion into the research taxonomy is **not** the same as declaring full runtime
playback support. The system may understand and study a trombone before it has a
trombone-specific generator, feasibility model, articulation grammar, samples, or
renderer. These capability layers should be added progressively from evidence rather
than fabricated from another instrument.

User direction can override research priority, but the default discovery policy is
autonomous and gap-driven.


## Baseline research instrument set

The initial research taxonomy is not limited to the currently executable trio/solo
players. The following instruments are first-class baseline research targets:

- piano
- acoustic/upright bass
- drums
- saxophone
- trumpet
- guitar
- electric bass
- vocal
- flute

The five newly seeded targets (trumpet, guitar, electric bass, vocal, flute) enter
at the **research/recognition** layer immediately. Dedicated generation,
instrument-specific feasibility, articulation grammar, rendering, and player
implementation may mature independently.

Acoustic bass and electric bass remain distinct instrument identities because their
physical constraints, articulation vocabulary, groove grammar, sustain behavior,
and role priors can differ substantially.

The catalog remains open-set. Instruments outside this baseline can still be
discovered and promoted from repeated cross-source evidence.
