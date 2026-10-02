# UMR v1.46 — Ensemble Runtime Loop

## Purpose

v1.43 introduced Shared Ensemble State and v1.44 introduced the Interaction
Scheduler. v1.46 connects them to the realtime app's player boundary.

The runtime loop is the first executable contract for AI trio / quartet
coordination.

## One runtime cycle

1. Freeze one immutable EnsembleState snapshot.
2. Compute every InteractionDirective from that same snapshot.
3. Give each active player the same snapshot plus its own directive.
4. Each player performs its own candidate generation/evaluation.
5. Each player returns only its immediately committed decision.
6. After every provider has decided, publish their intents/interactions.
7. Collect RenderGestures for the realtime renderer.
8. Listen/update state and run the cycle again.

## Why publication is atomic

If piano were allowed to update EnsembleState before bass decided, while drums
saw both piano and bass updates, the result would depend on software iteration
order rather than musical time.

v1.46 prevents this. All players in one decision cycle hear the same generation.

## PlayerRuntimeDecision

A decision contains:
- player ID;
- committed PlayerActionIntent;
- zero or more immediate RenderGestures;
- optional InteractionEvents.

It cannot be provisional at the app boundary. A player may maintain provisional
candidates internally, but only a committed current action crosses into runtime.

## Player adapter responsibility

The realtime app does not know how a player makes music.

A piano adapter may combine:
- piano grammar;
- harmony guidance;
- interaction directive;
- voice leading;
- physical feasibility;
- style policy.

A bass adapter may use walking/two-feel/pedal logic.

A drum adapter realizes SUPPORT / SETUP / TRANSITION using its own kit grammar.

The runtime loop only coordinates timing and state publication.

## Initial trio target

The first practical integration target is:

Piano + Bass + Drums

All three consume:
- chart / transport;
- shared harmony state;
- shared EnsembleState;
- InteractionDirective.

Each returns a committed RenderGesture. Once this path is stable, Sax can be
added as the foreground player without changing the runtime contract.

## Causality

Already committed/played actions are immutable.

Future plans remain private and provisional inside each player. A subsequent
runtime cycle can revise them after new ensemble evidence arrives.
