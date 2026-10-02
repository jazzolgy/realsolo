# AI Bassist — Standard 100 Practice Session 01

## Scope

Practice volume:
- 100 jazz standards
- 8 passes per standard
- 800 generated choruses
- temporary practice input: accessible text chord-chart mirror derived from the
  jazz-standard/iReal ecosystem
- canonical Shared Core source remains the CC BY 4.0 iRealPro Corpus v1.0
  registered under Standard 100

This session stores only aggregate practice findings. It does not copy the
source chord charts into the bass workstream.

## Curriculum passes

1. root / two-feel foundation
2. two-feel approach
3. basic walking
4. mixed walking
5. anti-template
6. approach restraint
7. contour discipline
8. integrated

## Aggregate findings

Two-feel:
- non-root/fifth color use on second pulse: 0.0 in the current conservative setup
- high-register excursion: 0.0
- repeated-pitch rate: ~0.096
- template repetition remains high (~0.467), which is acceptable only insofar as
  two-feel is intentionally stable; do not solve this by reintroducing frequent
  thirds/sevenths.

Basic walking:
- bar role-template repeat rate: 0.253
- directed approach/anticipation event rate: 0.353
- sustained same-direction motion rate: 0.144
- long step-chain rate: 0.030
- high-register excursion: 0.0

After anti-template + approach restraint + contour discipline in the practice
simulation:
- role-template repeat rate: ~0.008
- directed approach/anticipation rate: ~0.282
- sustained same-direction motion rate: ~0.079
- long step-chain rate: ~0.032
- high-register excursion: 0.0

## Main lesson

Anti-template pressure alone does not solve formulaic walking. It can eliminate
the exact role grid while leaving a new formula dominated by last-beat
approaches.

Therefore the player needs separate memories/budgets for:
- role-template repetition
- directed-approach density
- contour-direction fatigue

These controls should remain soft. Harmonic necessity and voice-leading may
override them.

## Code feedback applied

v1.53 applies two changes directly to the real Bass immediate realizer:

1. recent approach budget
   - if two directed targets have already occurred in the last eight committed
     bass roles, another approach/anticipation receives a soft penalty.

2. soft contour fatigue
   - after two consecutive moves in one direction, another same-direction move
     receives a small penalty before the stronger 3+ move recovery rule applies.

Two-feel remains conservative:
- root/fifth center
- restrained next-root anticipation
- low-priority third/seventh color
- contour reversal without forced harmonic color

## Next practice target

The remaining weakness is route vocabulary.

Current Bass can vary:
- root
- fifth
- chord member
- chromatic approach
- direct anticipation

It does not yet have enough shared instrument-neutral scalar/diatonic connection
affordances to generate the full variety implied by method-book walking
practice without inventing a private bass harmony engine.

The next Core/Bass step should expose shared linear-connection affordances
(diatonic passing, neighbor, enclosure/connector semantics) and let Bass realize
them physically.
