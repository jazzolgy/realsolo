# Decision / Context Logging and Ensemble Re-perception

RealSolo needs to listen again after every committed action. That is different
from deciding whether the previous action was "good" and changing long-term
learning.

This slice deliberately implements the first requirement and postpones the
second.

## Runtime loop

```text
Perceive
  ↓
Current Context
  ↓
Generate Candidates
  ↓
Evaluate
  ↓
Commit ONE Event / Action
  ↓
Observe ensemble again
  ↓
Refresh Shared Ensemble State
  ↓
next immediate decision
```

No reward, success score, causal-attribution score, or automatic long-term
learning update is created by this loop.

## DecisionRecord

An append-only decision record may preserve:

- player and decision kind;
- ensemble context snapshot;
- considered candidates;
- candidate score components;
- selected candidate and score;
- prior contributions;
- contextual gate weights;
- evaluator reasons;
- provenance.

This makes a later offline study possible without forcing a self-learning
architecture into the live path.

## PostEventObservation

After the event is played and the ensemble is heard again, the system may log a
new context snapshot linked to the decision.

It records **what happened next**, not **whether the previous decision was
successful**.

```text
DecisionRecord
      ↓
committed / played action
      ↓
new perception
      ↓
PostEventObservation
```

The relation can later be analyzed offline if there is evidence that outcome
learning improves musical behavior.

## Ensemble re-perception

`EnsembleObservation` and `reperceive_ensemble_state()` update Shared Ensemble
State with newly observed facts such as:

- ensemble density;
- energy;
- tension;
- available space;
- current leader;
- harmonic-state reference;
- newly observed player intents;
- interaction events.

This is short-term adaptation, not training.

For example, if the drummer becomes more active after the piano plays, the next
piano decision can immediately see the higher density/activity state. The
system does not automatically conclude that the piano caused the drummer's
behavior or that the piano's previous choice was good/bad.

## Architectural boundary

```text
real-time:
observe → decide → commit → re-observe → adapt

offline, optional later:
decision logs + post-event observations
→ research / human review / controlled evaluation
→ only then consider feedback learning
```

This keeps the live ensemble system causal and responsive without introducing
an unvalidated self-reward loop.
