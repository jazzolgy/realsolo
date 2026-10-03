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
