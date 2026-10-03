# Contextual Prior Gating

Hierarchical priors are now dynamically attenuated by the current musical
situation.

The principle is:

```text
learned history suggests
live context decides how much to listen to that history
```

A prior is never deleted or rewritten. Runtime receives a gated view with lower
layer weights.

## Inputs to the gate

- ensemble complexity;
- confidence in current live evidence;
- written-material priority;
- structural/form constraint;
- performance mode.

## Improvisation

During open improvisation, dense ensemble activity, reliable current interaction
evidence, and strong phrase/form constraints reduce the authority of historical
priors.

Domain priors are attenuated least. Genre/style/legend priors are attenuated
more strongly because they should not override what the ensemble is doing now.

## Head performance

Head performance uses the strongest gating.

```text
Written Head Identity
    >
Head Fidelity Guard
    >
Live ensemble / harmonic context
    >
Genre / Style / Legend prior
```

STRICT head mode closes improvisation priors most strongly. NATURAL remains
conservative. LOOSE allows more stylistic influence but still keeps the written
melody authoritative.

## Runtime integrations

### Piano solo

The live gate is derived from:

- ensemble density;
- left-hand comping activity;
- phrase-space confidence;
- ensemble-complementarity confidence;
- turn-taking confidence;
- phrase maturity;
- tension.

The resulting gate attenuates both the learned solo-domain prior and legend
biases before candidate scoring.

### Piano comping

The hierarchy is gated from current ensemble density, soloist/drummer activity,
phrase-boundary evidence, interaction availability, and harmonic-turn
confidence before domain/genre/style density priors are composed.

### Interaction scheduler

The learned response-role prior remains a confidence nudge only. Strong recent
interaction evidence and dense ensemble state reduce that nudge.

### Groove

The groove prior can still supply a default grammar when no explicit grammar is
provided, but its confidence influence is gated. An explicit runtime
`grammar_id` remains authoritative.

## Non-negotiable rule

Contextual gating may **attenuate** configured prior weights but never amplify
them beyond their base values.

This prevents a learned corpus tendency from becoming more authoritative merely
because the current context is uncertain.
