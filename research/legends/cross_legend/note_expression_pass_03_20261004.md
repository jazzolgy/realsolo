# Bill Evans / Charlie Parker note-expression pass 03

## Start-state safety check

This continuation re-read `docs/ARCHITECTURE.md` and started against main
`762fa05c243867ec9afbc1a5fe3cbcfed7b7d41e`. The existing pass-02 branch is exactly one research-document commit
ahead and zero behind main. Open integration work still touches Audio Evidence,
RealChord/FormGraph, Shared Vocabulary, Parker vocabulary, and quartet runtime,
so this pass deliberately avoids those contract/code surfaces.

## What could be advanced safely

The private project audio referenced by both source manifests is not exposed in
this execution workspace. Therefore this pass does **not** invent a second set of
literal note events for the queued source intervals.

The committed evidence does, however, permit a stronger coverage audit:

### Charlie Parker

Queued provenance interval: **181.421–359.277 s** (177.856 s).

The existing album-level analysis already characterizes the encompassing second
segment (approximately 179.886–360.995 s) as:
- tempo proxy 117.5 BPM,
- 2.289 detected onsets/s,
- harmonic/percussive RMS ratio 0.952,
- 10-second activity CV 0.150.

These measurements remain `OBSERVATION_ONLY` mixed-recording evidence. They do
not establish Parker sax note identity, articulation, microtiming, or a reusable
lick. They do establish that the next literal pass should expect a substantially
sparser salient-event surface than track 01 and should not tune the detector or
runtime toward the previous segment's density.

A rough segment-level expectation of about **407 salient onsets**
(177.856 × 2.289) is recorded only as a QA envelope, never as extracted events.

### Bill Evans

Queued provenance interval: **BE-001 Waltz For Debby 120.000–413.000 s**
(293.000 s).

The repository already contains a whole-playlist mixed-audio pass with 26,758
onsets and 97,547 pitch hypotheses over 7,717.956 s. This proves broad acoustic
coverage exists, but it is intentionally not treated as Bill Evans piano
transcription: the aggregate explicitly withholds instrument attribution and
runtime promotion.

Therefore the next local/private pass should intersect the existing full-source
event store with BE-001 120–413 s rather than re-detecting the entire recording.
Only after that intersection should it perform source/instrument attribution and
MusicalScoreCoordinate alignment.

## New research observations

1. **Detector calibration must be segment-relative.** Parker segment 02's
   committed onset-density proxy is far below the already studied track-01
   interval. Fixed density assumptions would bias both transcription QA and
   learned phrase-density priors.
2. **Full-source coverage is not musical coverage.** Bill Evans has a large
   whole-playlist note-hypothesis aggregate, yet the requested learning remains
   incomplete because WHAT events are not reliably attributed and WHEN lacks
   score coordinates.
3. **Coverage needs two axes:** acoustic-event coverage and promotion-ready
   musical coverage. A source can be 100% acoustically scanned and still 0%
   eligible for Legend prior promotion.
4. **Expression evidence must attach after identity/alignment.** RMS/body/accent
   proxies from a mixed recording may be retained as source observations, but a
   Bill Evans or Parker expression profile requires attributed events and
   same-position/form comparison.
5. **Comping transfer boundary:** ensemble texture can inform Shared Core
   decisions such as leave-space / reduce-candidate-density. It cannot determine
   piano voicing, touch, hand allocation, or note body; those remain Piano Player
   realization.

## Required schema for the next private event extraction

For every newly verified event, store:
- provenance: source_id + source-time locator,
- `MusicalScoreCoordinate`: song, arrangement segment, section, form bar,
  beat, subdivision, recurrence, performance phase,
- WHAT: pitch/interval/contour/motif identity with confidence,
- WHY: harmony target, phrase role, tension/release, ensemble role,
- HOW: relative dynamic, accent, note body, timing emphasis, foreground weight,
- attribution: source instrument hypothesis + confidence,
- evidence state: `OBSERVATION_ONLY` until promotion gates are satisfied.

Literal transcription and expression profiles remain separate artifacts.

## Runtime implications — not yet promoted

The evidence supports testing, but not hard-coding:
- ensemble-density-aware pruning of immediate candidates,
- more deliberate space when support layers are already occupied,
- motif identity matching that tolerates changed HOW realization,
- Piano comping body/touch evaluation after Shared Core semantic selection.

All continue to obey **Plan intention, not notes** and one-event commitment.

## Coverage ledger

| Source | Literal/private event status | Musical-coordinate status | Promotion |
| --- | --- | --- | --- |
| Parker track 01, 0–178.352 s | existing hypotheses | not fully aligned | OBSERVATION_ONLY |
| Parker track 02, 181.421–359.277 s | **queued; not fabricated here** | pending | blocked |
| Evans BE-001, 0–120 s | existing hypotheses | not fully aligned | OBSERVATION_ONLY |
| Evans BE-001, 120–413 s | whole-source scan exists; interval extraction/attribution pending | pending | blocked |

## Next queue

1. Parker 181.421–359.277 s: extract actual events from private audio, compare
   observed onset count with the ~407 QA envelope, then align beat/bar/form.
2. Evans BE-001 120–413 s: subset existing private whole-source hypotheses first;
   avoid redundant full-source detection.
3. For both, perform attribution before Legend labeling.
4. Detect repeated WHAT identities and compare their HOW profiles separately.
5. Promote only recurrence-supported, score-aligned tendencies; keep literal
   source phrases out of runtime playback.
