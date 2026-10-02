# AI Bassist v1.37 — Immediate Realization Vertical Slice

## Goal

Establish the bass workstream without duplicating Shared Core intelligence.

The first implementation answers a deliberately narrow question:

> Given the current Shared Core harmonic state and the immediately previous bass
> action, what bass actions are playable **now**?

It does not answer "what four-bar bass line should be generated?"

## Architectural boundary

Shared Core remains authoritative for:

- Expected / Observed / Inferred Harmony
- functional meaning and harmonic affordances
- contextual tension
- generic voice-leading
- form / phrase / narrative / memory
- ensemble state
- future-harmony awareness

The bass layer realizes those shared meanings as bass-specific behavior:

- root / non-root choice
- walking vs two-feel vs pedal behavior
- chromatic connection toward an already-known future target
- playable register
- duration
- later: articulation, note length, microtiming and instrument physics

No shared-core file is changed by this slice.

## Runtime

```
HarmonicFrame + BassContext
    -> immediate bass candidate family
    -> shared voice-leading evaluation
    -> bass-specific scoring
    -> choose one immediate action
    -> listen again / rebuild context / re-plan
```

Future harmony is allowed to influence a current approach tone, but an exact
future sequence is never stored.

## Evidence precedence

For immediate root/chord evidence, the bass realizer consumes:

```
Inferred -> Observed -> Expected
```

This is a realization policy over already-separated Shared Core evidence, not a
new harmony inference engine.

## Initial candidate grammar

### Walking

Current-event candidates may include:

- root
- perfect fifth only when current pitch-class evidence supports it
- other pitch classes already present in Shared Core evidence
- lower/upper chromatic approach to a known next root near the end of the measure
- direct next-root anticipation

### Two-feel

The current baseline uses a two-beat event duration and a deliberately smaller
root/fifth-centered candidate family. This is only scaffolding; learned two-feel
placement and interaction remain research work.

### Pedal

The baseline emits the current harmonic root as the pedal anchor. Functional
pedal semantics (tonic vs dominant pedal, retained pedal across chord change)
should be added only when Shared Core exposes the required shared state cleanly.

## Important failure prevented

A naive jazz-bass rule such as "always allow root and perfect fifth" is not
safe. For example, a half-diminished sonority may explicitly contain a lowered
fifth. v1.37 therefore allows the perfect-fifth candidate only when Shared Core
pitch-class evidence supports it.

This keeps chord semantics in Core and instrument realization in Bass.

## Tests

`tests/test_v137_bass_immediate_realizer.py` covers:

- walking candidates and bass register
- inferred-harmony precedence
- rejection of a false perfect fifth when evidence contradicts it
- late-measure approach / anticipation without a frozen future line
- two-feel immediate duration
- pedal anchoring

## Next research steps

1. Replace the simple candidate weights with a bass-specific PerformanceGrammar.
2. Model note length separately from nominal beat duration.
3. Add walking-bass transition features: metric role, target type, interval,
   direction, repeated-note pressure, register trajectory, and cadence position.
4. Add drummer coupling: ride/hi-hat/kick evidence, shared pulse placement, and
   microtiming relationship rather than isolated bass timing.
5. Add ensemble-density response and deliberate space/repetition behavior.
6. Build bass LegendProfiles as contextual decision tendencies rather than
   stored/transplanted lines.
7. Add acoustic/electric bass InstrumentProfiles and physical constraints.
8. Promote any newly discovered instrument-neutral concept through
   `CORE_CHANGE_REQUEST.md`, never by silently forking Core.
