# Quartet Shared Intelligence Integration Status

This document tracks whether research/learning/player intelligence is actually
used by the audible realtime quartet path.

## Connected in this integration slice

- same-snapshot / one-event causal runtime
- Jazz Jam Session convention
- role-aware Shared Groove projection
- real metric position and tempo delivered to Players
- Bass quarter-note walking harmonic spine
- Bass swung-offbeat ghost/dead-note opportunity path
- Shared local-key context delivered to Bass
- Shared harmonic reasoning delivered to Piano
- Shared harmonic-turn / ensemble evidence delivered to Piano comping
- Shared Solo Runtime delivered to Sax
- Shared Solo Grammar delivered to Sax
- Shared Motif Policy + MotifMemory delivered to Sax
- MusicalPolicyProjection facade delivered to Sax
- contextual prior gating plumbing delivered to Sax
- bebop score/style context delivered to quartet
- Bebop Drum Runtime used for bebop quartet
- Drum ride continuity memory
- Drum snare phrase memory
- Bass/Drums coupling projection

## Present but not yet fully active

### Hierarchical learned priors

The runtime contracts are now present:

- learning_prior_runtime.py
- hierarchical_priors.py
- contextual_prior_gating.py
- musical_policy_projection.py

However the Autumn Leaves benchmark does not yet construct a populated
HierarchicalPriorSet from a promoted runtime learning store. An optional
`hierarchical_priors` context can now reach the Sax projection, but no benchmark
prior is invented merely to make the path non-empty.

Reason: evidence-only research must not be silently promoted to authoritative
runtime policy.

### Legend / vocabulary

Parker, Bill Evans and Scott LaFaro profiles/vocabulary exist, but the canonical
quartet still does not automatically impose a named legend on every performance.

Reason: Legend is a narrower style layer and should be an explicit or
context-selected soft prior, not a hard default for generic jazz.

Next integration should provide a shared legend/vocabulary selector and allow
all Players to consume transferable dimensions.

### MusicalMoment / DecisionContextLog

These remain on the later research/audit branch stack and are not yet present in
this audible branch.

Reason: they are observational/audit representations and do not need to block
musical integration. They should be ported after the decision path is stable so
we can inspect what each Player actually used.

### Full Piano research stack

Piano now receives Shared harmonic reasoning and Shared harmonic-turn context,
while its existing comping evaluator still owns:

- harmonic continuity
- creative continuity
- LH texture / voice leading
- RH/LH interaction
- role occupancy
- variation
- ensemble response

Still missing from the live benchmark:

- reliable soloist register evidence
- shared vocabulary/legend priors
- promoted learned comping priors
- cross-player motif identity beyond coarse continuity indication

### Full Drum research stack

The live bebop path now uses ride/snare memory and bass coupling. Still not
injected:

- named drummer LegendProjection
- shared vocabulary intents
- calibrated chorus-scale memory updates
- explicit trading/solo mode unless the session requests them

### Head / Intro / Human Drift

Not active in this Autumn Leaves open-solo benchmark by design.

- Head Fidelity requires written head material.
- Intro intelligence requires an intro/session request.
- HUMAN_DRIFT remains off until fixed-tempo quartet behavior is musically stable.

## Invariant

Runtime should eventually look like:

```text
promoted Learning / Genre / Style / Legend / Vocabulary
                    ↓
          Shared musical reasoning
                    ↓
  Harmony / Form / Turn / Motif / Interaction
                    ↓
          MusicalPolicyProjection
                    ↓
     Player-specific candidate evaluation
                    ↓
           ONE immediate commitment
                    ↓
       Shared Groove / Realtime projection
                    ↓
                  audio
```

Research files existing in the repository is not sufficient. A feature counts
as "connected" only when the audible runtime consumes it through this path.
