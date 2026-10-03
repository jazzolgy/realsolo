# Bill Evans / Charlie Parker note-expression pass 02

## Scope and evidence gate

This pass starts from main `762fa05c243867ec9afbc1a5fe3cbcfed7b7d41e` and intentionally does **not** invent new
note events. The private project audio referenced by the source manifests is not
available in the current execution workspace, so the next unprocessed source
intervals cannot be acoustically re-run here.

Existing committed aggregate evidence is used only for a cross-legend research
pass. All conclusions below remain `OBSERVATION_ONLY`. Exact source seconds are
provenance/navigation only; none are promoted as a musical learning address until
a `MusicalScoreCoordinate` alignment exists.

## Covered evidence

- Charlie Parker compilation track 01, provenance interval 0.000–178.352 s:
  711 detected onsets, 3,411 multi-pitch hypotheses, median IOI 0.2090 s.
- Bill Evans, BE-001 *Waltz For Debby*, provenance interval 0.000–120.000 s:
  454 detected onsets, 2,063 multi-pitch hypotheses, median IOI 0.2322 s.

No additional literal note hypotheses are claimed in this pass.

## Aggregate comparison

The Parker mixed-band segment has a higher observed onset rate (4.0089/s versus
3.7899/s) and shorter median IOI (0.2090 s versus 0.2322 s). This is compatible
with a denser foreground event stream, but **must not** be interpreted as a
Parker-versus-Evans player trait because both recordings are mixed ensembles and
instrument attribution is unresolved.

The Evans segment shows a larger median harmonic-body proxy (2.6504 versus
2.2450) and a lower mean spectral centroid (1256.68 Hz versus 2287.0 Hz).
This is useful as a recording/texture discriminator and possible voicing-body
cue, not yet as a Bill Evans piano prior.

Both segments contain high counts of alternating contour trigrams. Parker's
aggregate leaders include down-up-down and up-down-up; Evans' leaders include
flat-up-down and up-down-flat. These are candidates for a future
score-aligned **contour-operation** study, not reusable licks.

## WHAT / WHEN / WHY / HOW separation

### WHAT
Do not promote the CQT peak sets as literal vocabulary. They remain candidate
events pending source separation, instrument attribution, and score alignment.

### WHEN
The next required operation is to map verified foreground events to
`MusicalScoreCoordinate(song, arrangement_segment, form_section, form_bar,
beat, subdivision, recurrence_index, performance_phase)`. Timestamp-only
similarity is insufficient.

### WHY
For each aligned phrase, future passes should label target behavior,
tension/release role, phrase role, and ensemble response before deriving a
Legend prior.

### HOW
Keep relative expression independent from note identity:
dynamic contour, onset/accent contour, harmonic/body contour, timing emphasis,
foreground weight, and space. Repeated motifs must receive separate HOW profiles
so identity can remain stable while realization changes.

## Runtime transfer candidates

Only these instrument-neutral questions are admitted for later verification:

1. **Density-relative candidate pruning** — when the current ensemble is dense,
   prefer fewer immediate candidates and more space; this is a Shared Core
   hypothesis, not a Legend trait.
2. **Contour identity / expression independence** — motif recognition should not
   require identical accent, body, or dynamic realization.
3. **Body-aware comping evaluation** — Piano may evaluate voicing/touch body as
   a realization dimension, while Shared Core supplies only semantic intention.
4. **One-event commitment** — learned contour or target tendencies may bias the
   next candidate, but may never expand into a precomposed note sequence.

These are research hypotheses only. No runtime weights are changed by this pass.

## Remaining queue

1. Charlie Parker: provenance interval 181.421–359.277 s.
2. Bill Evans BE-001: provenance interval 120.000–413.000 s.
3. For both: source separation / attribution -> beat/bar/form alignment ->
   repeated-motif identity matching -> separate expression-profile comparison.
4. Re-check open integration PRs before any runtime promotion. In particular,
   avoid touching canonical Audio Evidence, RealChord/FormGraph, or shared
   vocabulary contracts while their integration branches remain open.

## Conflict note

At pass start, main was `762fa05c243867ec9afbc1a5fe3cbcfed7b7d41e`. Open PRs include active work on Audio
Evidence, RealChord/FormGraph, Shared Vocabulary, and Parker vocabulary
promotion. This pass therefore changes research documentation only and avoids
those code/data contract surfaces.
