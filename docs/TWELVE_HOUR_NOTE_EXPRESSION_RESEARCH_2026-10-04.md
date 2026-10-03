# 12-hour Bill Evans / Charlie Parker note-expression research pass — 2026-10-04

Goal: exhaust the **remaining** uploaded-audio regions into private note/event hypotheses plus public, non-reconstructive research aggregates, while preserving provenance, confidence and the current Shared Core architecture.

## Non-negotiable invariants

- Re-read `main` HEAD and `docs/ARCHITECTURE.md` at the start of each hourly pass and again immediately before merge.
- Never blind-merge old stacked branches. Port only compatible work onto current `main`.
- Learning/comparison address = `MusicalScoreCoordinate`; source seconds are locator/provenance only.
- Mixed recordings remain `OBSERVATION_ONLY` until instrument attribution is reliable.
- Exact note-event hypothesis files stay private/local; repository artifacts store coverage, counts, abstractions, confidence and non-reconstructive statistics.
- Literal note identity and `expression_profile` are separate.
- Runtime remains causal: **Plan intention, not notes**. No exact future-note phrase replay.

## Hourly execution sequence

1. HEAD / architecture / open-PR collision audit.
2. Read coverage ledgers; choose only the next unprocessed interval.
3. Extract onset + multipitch hypotheses and expression proxies:
   - source-time locator
   - beat/form address when aligned
   - local RMS / relative level
   - onset strength / accent proxy
   - harmonic-body proxy
   - spectral/register proxy
   - local silence and phrase-boundary evidence
4. Save exact event hypotheses privately.
5. Derive public research observations:
   - interval/contour/rhythm distributions
   - repeated motif/lick candidate hashes
   - phrase density / space morphology
   - dynamic/accent/body/timing relationships
   - motif recurrence + HOW variation when alignment supports it
6. Update legend-specific coverage/status and evidence labels.
7. Promote only repeated, well-supported abstractions into Legend Vocabulary / expression evidence.
8. If a behavior is cross-legend/instrument-neutral, propose/implement Shared Core improvement.
9. Run tests; create/update PR.
10. Re-read `main` HEAD before merge; merge only with passing CI and no conflict.

## 12-pass target allocation

- Pass 1: establish coverage ledger; Parker track 1; Bill Evans BE-001 opening.
- Passes 2–5: Charlie Parker compilation remaining tracks/regions, prioritizing exact-note hypotheses, phrase-space, articulation/accent proxies and repeated lick/motif candidates.
- Passes 6–9: Bill Evans playlist tracks excluding already-studied Autumn Leaves head/solo windows; prioritize score-match tunes and piano/comping/expression evidence.
- Passes 10–11: cross-source recurrence: same/similar motif family -> expression variation; comping texture/attack-density/body relationships; Parker line grammar vs Evans piano realization.
- Pass 12: coverage audit, unresolved list, promotion gate, runtime listening-policy update only where evidence is sufficient.

## Desired outputs

Private/local:
- event-level note hypotheses with source-time locator and confidence.

Repository:
- coverage ledgers
- non-reconstructive interval/rhythm/contour/expression aggregates
- motif/lick family identifiers and transformation labels without reconstructive note dumps
- form/bar/beat aligned observations where alignment is verified
- Legend-specific expression/vocabulary candidates
- tests for any runtime/Shared-Core change
