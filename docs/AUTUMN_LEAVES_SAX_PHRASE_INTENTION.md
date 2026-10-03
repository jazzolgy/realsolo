# Autumn Leaves Sax Phrase Intention v0.1

The first canonical quartet proved the causal runtime, but its Sax path was too
close to "pick a safe chord tone every eighth-note tick." This patch changes the
decision structure without abandoning one-event causal improvisation.

## Principle

```text
form / local key / next harmony
        ↓
phrase-level intention
        ↓
current-event route biases
        ↓
generate immediate candidates
        ↓
commit ONE event
        ↓
hold / listen again
```

Phrase intention never stores a future note sequence.

## Autumn Leaves context

The benchmark supplies:

- G-minor / relative-Bb-major local pitch collection;
- next-harmony guide-tone targets (3rd / 7th when available);
- A/B section;
- four-bar phrase maturity;
- swing + bebop score/style context.

No head melody is embedded.

## Sax phrase phases

The current causal phrase state cycles through:

- `attack` — establish direction without immediately over-weighting CHORDAL;
- `develop` — passing, chromatic passing, approach and enclosure routes compete;
- `target` — next-harmony guide-tone arrival is emphasized;
- `release` — longer duration, stable arrival and real space become competitive.

These are soft route/duration/space biases, not a prewritten bebop line.

## Rhythm

The Sax no longer treats every listening tick as a required new eighth note.

Phrase intention may choose:

- 0.5-beat event;
- 1.0-beat event;
- 1.5-beat release event;
- intentional rest.

When an event occupies more than one decision tick, later ticks publish
`sax_sustain_hold` rather than choosing a second overlapping Sax note. A hold
remains semantically active so Piano/Bass/Drums do not mistake a sustained note
for silence.

## Interaction

True rest and held-note continuation are separate states:

```text
REST
→ density 0
→ accompaniment may take more space

SUSTAIN HOLD
→ soloist remains active
→ accompaniment should still respect foreground occupancy
```

## Still intentionally missing

This patch does not yet connect a specific LegendProfile/vocabulary memory into
the quartet benchmark. The next listening pass should first determine whether
phrase continuity, target motion, duration variety and space improved before
adding legend-specific priors.
