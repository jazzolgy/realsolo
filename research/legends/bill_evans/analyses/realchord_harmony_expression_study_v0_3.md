# Bill Evans — RealChord-conditioned HOW Study v0.3

## What changed

RealChord 1350 is now available to Shared Core as a symbolic corpus reference.
For the project source `Jazz 1350.html`, Autumn Leaves is source-order
`realchord_id=96`, key `G-`, style `Medium Swing`.

This pass connects that stable song identity to the existing Bill Evans
Autumn Leaves form/expression work.

The important distinction is:

```
RealChord      -> Expected Harmony / structural reference
performance    -> Observed Harmony
reasoning      -> Inferred Harmony
```

Expected harmony never overwrites what Bill Evans and the trio actually played.

## Canonical research address

The expression study should now converge on:

```
realchord_id
+ form bar
+ beat
+ chorus / recurrence
+ performance phase
+ motif state
+ ensemble state
```

Seconds remain only a locator into source audio.

For Autumn Leaves the existing performance analysis already has a verified
32-bar form with A1 / A2 / B / C navigation windows. RealChord supplies the
stable chart identity, but its raw section/repeat encoding must be structurally
normalized before its own section labels are treated as authoritative.

Therefore we do **not** silently rewrite A1/A2/B/C from the current Bill Evans
alignment to match an unparsed RealChord chart.

## New comparison experiment

The previous study compared:

```
same form bar, head vs solo
```

The stronger experiment is:

```
same RealChord expected harmony
x same form bar / beat
x different performance phase
-> HOW difference
```

The HOW vector remains multi-dimensional:

- dynamic proxy
- accent proxy
- note-body proxy
- brightness/register proxy
- foreground weight
- timing emphasis
- space/release behavior

This lets the model ask whether a difference comes from:

- harmonic position,
- performance phase,
- motif development,
- ensemble density,
- substitution/reharmonization,
- or Bill Evans-specific expressive choice.

## Why Expected / Observed / Inferred separation matters

If RealChord says the expected chart harmony is X but the performance produces
a substitution or reharmonization, the research record should become:

```
Expected: RealChord X
Observed: performance Y
Inferred: functional interpretation Z
HOW: expression vector
```

That is much more useful than replacing X with Y or pretending the chart was
wrong.

It allows questions such as:

- Did the expression intensify because of form position even though harmony was
  unchanged?
- Did a reharmonized event carry a different attack/body profile?
- Did a repeated motif keep its contour while changing expression because the
  current harmony or ensemble role changed?

## Motif-expression memory connection

For a returning motif A, the research target is now:

```
motif identity A
+ RealChord expected harmony
+ observed/inferred harmony
+ form position
+ previous HOW state
-> current HOW realization
```

This preserves the earlier principle that motif identity and expression profile
are separate memories.

The system should be able to learn:

```
A over expected ii-V:
  chorus 1 -> medium foreground, sharper accent

A' at the same chart location later:
  lower absolute dynamic, longer body, brighter register, more space
```

without storing or replaying an exact future note sequence.

## Current evidence status

The RealChord source identity for Autumn Leaves is usable now.

The exact RealChord raw chart still needs structural normalization into measures,
beats, repeats/endings, and chord events before chord-by-chord Bill Evans
expression claims can be made directly from that source.

Until then:

- `realchord_id=96` may be attached as stable repertoire identity;
- existing 32-bar score alignment remains the verified performance map;
- exact expected chord labels must come only from a normalized RealChord record,
  not from memory or guesswork.

## Next automatic pass once normalization is available

For each aligned head/solo bar:

1. resolve RealChord expected harmony at beat level;
2. attach observed/inferred harmony independently;
3. attach motif state if available;
4. attach HOW vector;
5. compare same expected harmony across chorus/phase;
6. search for repeated Bill Evans tendencies;
7. keep one-off/tune-specific behavior below promotion threshold.

The intended learning object is therefore no longer merely
`form_bar -> dynamics`, but:

```
harmonic context
x form position
x phrase/motif state
x ensemble role
-> expressive realization
```
