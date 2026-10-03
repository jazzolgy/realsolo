# Bill Evans + Charlie Parker 12-hour deep-listening campaign — 2026-10-04

## Goal

Use the owner-supplied Bill Evans and Charlie Parker project audio to extend only
the still-missing note/event coverage, then convert that evidence into
non-reconstructive musical knowledge for RealSolo:

- note/event hypotheses and timing;
- phrase/motif/pattern/lick abstractions;
- rhythm and target behavior;
- dynamics, accent, note body and timing-expression evidence;
- ensemble interaction and phrase-space evidence;
- Bill Evans comping / piano-HOW evidence;
- Charlie Parker solo / linear-language evidence;
- transferable Shared vocabulary and expression priors.

This campaign does **not** treat mixed-audio automatic multipitch output as
ground-truth transcription. Exact event hypotheses remain private/local unless
there is an explicit rights decision to publish them. Public repo artifacts stay
aggregate, abstract, provenance-aware and non-reconstructive.

## Invariants

1. Re-read current `main` head and `docs/ARCHITECTURE.md` before each batch.
2. Never blind-merge an old player/research branch into current main.
3. Seconds are source locators only. Musical learning requires
   `MusicalScoreCoordinate` when alignment is known.
4. Unknown instrument attribution stays unknown. Mixed trio/full-band evidence
   is not silently labeled as Evans piano or Parker alto.
5. Separate:
   - WHAT: note/motif/vocabulary identity
   - WHEN: form/section/bar/beat
   - WHY: harmony/phrase/tension/ensemble role
   - HOW: dynamic/accent/body/timing/foreground.
6. Literal vocabulary identity and expression profile are stored separately.
7. Runtime remains one-event-now: no exact future phrase replay.
8. Before every merge: read main head again, compare branch/base, run tests,
   merge only if current and conflict-free.

## Current coverage baseline

### Bill Evans

Project audio:
- `be_playlist_project_audio`: ~7717.956 s
- `be_best_full_album_project_audio`: ~3760.091 s

Already available:
- full-duration mixed-audio note-hypothesis aggregate over both files;
- playlist 0–120 s private/local note-hypothesis pass;
- Autumn Leaves selected head + solo windows with ~1700 pitch hypotheses;
- form-bar expression studies and RealChord-conditioned expression study.

Missing:
- persistent fine-grained note/event coverage for the rest of the two audio
  sources;
- track/form identity for many windows;
- pianist-only attribution;
- verified RH/LH/voicing membership;
- motif recurrence + HOW linkage across more than the existing Autumn Leaves
  windows.

### Charlie Parker

Project audio:
- `cp_audio_greatest_hits_project`: ~6448.056 s

Already available:
- 0–178.352 s private/local note-hypothesis pass;
- silence-boundary map over the compilation;
- phrase-space/turn-taking scans;
- aggregate Parker conditional and phrase-space priors from symbolic sources.

Missing:
- fine-grained note/event pass from ~181.421 s onward;
- track/form alignment for most compilation segments;
- Parker-vs-accompaniment attribution in mixed audio;
- expression contour and recurrence analysis tied to Parker-like foreground
  evidence.

## 12 hourly passes

### H1 — Inventory, collision check, extraction calibration
- read main head + architecture + manifests + coverage;
- verify audio presence and duration;
- regenerate a small known window for both legends;
- compare detector counts against prior stored summaries;
- lock extraction settings and checkpoint schema.

### H2 — Parker early missing tracks
- begin at 181.421 s;
- process successive silence-bounded tracks;
- store private event hypotheses;
- commit only non-reconstructive coverage, rhythm/expression aggregates.

### H3 — Parker middle I
- continue strictly from checkpoint;
- derive phrase cells, interval/rhythm fingerprints, target approach classes;
- find repeated/varied motif families without storing replayable phrase strings.

### H4 — Parker middle II
- continue note/event coverage;
- attach dynamic/accent/body proxies to motif recurrence;
- distinguish line density from attack intensity and foreground weight.

### H5 — Parker late
- finish remaining compilation intervals;
- build coverage completeness report;
- compare newly observed behavior with existing Parker conditional priors.

### H6 — Parker consolidation
- cluster transferable linear vocabulary;
- promote only evidence-supported conditional tendencies;
- update Shared solo/vocabulary research artifacts, not Player-local generic logic.

### H7 — Evans playlist missing coverage I
- continue after already studied regions;
- event hypotheses + expression windows;
- detect likely piano-foreground / comping-support windows conservatively.

### H8 — Evans playlist missing coverage II
- motif recurrence families;
- same/similar motif HOW comparison;
- comping attack-density, register/brightness, body, silence-before/after.

### H9 — Evans playlist missing coverage III
- finish playlist note/event coverage;
- identify track/form windows that can be aligned to score/RealChord;
- preserve unaligned windows as observation only.

### H10 — Evans second full-album source I
- fine-grained note/event pass over first half;
- compare source-level expression distributions with playlist source.

### H11 — Evans second full-album source II
- finish second source;
- extract comping/piano texture abstractions;
- build recurrence/HOW and form-position candidates where identity is known.

### H12 — Cross-legend consolidation + runtime value
- completeness audit;
- Parker line-language vs Evans motif/harmony/HOW separation;
- derive transferable Shared priors;
- add tests for any runtime-facing promotion;
- final collision/head check;
- open/merge only green, current PRs;
- write final campaign report with unresolved evidence gaps.

## Per-pass repository protocol

At the start:
1. fetch current `main` head;
2. read current `docs/ARCHITECTURE.md`;
3. inspect this campaign state file;
4. compare any active campaign branch against current main.

During work:
- use a new branch based on current main for substantive code/research changes;
- do not overwrite evidence produced by another pass;
- update coverage/checkpoint by append/merge semantics;
- exact event hypotheses remain local/private; public artifacts contain counts,
  distributions, abstractions, confidence, provenance and alignment status.

Before merge:
1. fetch main head again;
2. compare commits;
3. run full pytest;
4. if main moved incompatibly, reconcile on a fresh branch from current main;
5. merge only when CI is green and branch is current enough to avoid ownership
   regression.

## Success criteria after 12 hours

- every owner-supplied Evans/Parker audio interval has a coverage status;
- all newly processed intervals have event-count, rhythm, expression and
  provenance summaries;
- unresolved mixed-audio attribution is explicitly marked;
- form-aligned regions use canonical musical coordinates;
- motif/lick/pattern abstractions are linked to separate HOW profiles;
- Bill Evans research improves piano comping/HOW evidence without turning Evans
  into generic piano truth;
- Parker research improves Shared linear/solo priors without literal replay;
- all runtime-facing promotions are conditional, tested and collision-safe.
