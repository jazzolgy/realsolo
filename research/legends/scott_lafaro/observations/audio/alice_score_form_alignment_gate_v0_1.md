# Alice score/form alignment gate v0.1

## Purpose

Define the validation boundary between the existing private 60-event
`NOTE_HYPOTHESIS` store and `SCORE_ALIGNED_HYPOTHESIS`.

This gate does not contain event-level notes, times, or ordered confidences.

## Evidence roles

- The owner-supplied recording is the authority for performed time and heard
  events.
- `Realbk1.pdf p.12` is a harmony/form reference, not an exact performance
  timeline.
- The private performance-to-score map records deviations between those two
  evidence sources.

Do not rewrite an acoustic pitch hypothesis merely because it conflicts with the
lead sheet.

## Private performance-to-score map

Before event promotion, establish private anchors sufficient to distinguish
plausible form locations. The map may represent:

- count-in or intro material not represented by the chart;
- pickup placement;
- section/repeat traversal;
- local tempo drift;
- substitutions or reharmonization;
- tags, extensions, omissions, or other performance-form deviations.

Unknown anchors remain null. A missing anchor must not be replaced with a
fabricated bar or beat.

## Per-event alignment result

A private candidate may carry:

- one supported score/form location; or
- multiple explicit plausible alternatives with uncertainty; or
- no supported location yet.

The first two cases may satisfy the alignment evidence requirement. The third
remains `NOTE_HYPOTHESIS`.

A plausible alternative set is evidence of alignment uncertainty, not evidence
of instrument identity.

## Promotion checks

Promote to `SCORE_ALIGNED_HYPOTHESIS` only when all are true:

1. the ingestion gate passed for the original private store;
2. candidate identity, acoustic timing, and pitch hypothesis are preserved;
3. the assigned form/score location is supported by the private
   performance-to-score map;
4. expected harmony is labelled as score-derived evidence;
5. unresolved alternatives are retained rather than collapsed for convenience;
6. provenance identifies the score anchor and alignment method.

Never force 100% alignment coverage. Unresolved candidates remain at the prior
stage.

## Attribution boundary

Score compatibility alone cannot classify a candidate as Scott LaFaro.
Instrument attribution starts only after this gate and must separately consider
piano left hand, piano resonance, percussive leakage, overlap, and bass
fundamental/overtone evidence.

## Public-safe reporting

Public summaries may report only non-reconstructive aggregates such as:

- count aligned / unresolved / quarantined;
- coarse form-section coverage;
- counts of ambiguity classes;
- protocol/schema versions and provenance.

Do not publish the performance-to-score anchor times, candidate ordering,
candidate IDs, exact pitches, event times, or reconstructive phrase data.
