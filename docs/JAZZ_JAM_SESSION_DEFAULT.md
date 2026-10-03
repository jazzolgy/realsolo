# Jazz Jam-Session Default

Unless a higher-priority instruction says otherwise, **jazz performance in
RealSolo follows ordinary jam-session coordination conventions**.

This is a Shared Music Intelligence / ensemble-convention rule. It does not
belong to Piano, Bass, Drums, Sax, or Realtime individually because all players
must interpret the same session convention.

## Precedence

```text
explicit user / session instruction
        ↓
written score / chart instruction
        ↓
Jazz jam-session convention
        ↓
Genre / Style / Legend soft priors
        ↓
Player-specific realization
```

The default never overrides an explicit arrangement.

## Default jazz convention

When jazz is requested and no conflicting instruction exists:

- everyone shares the same song form and form location;
- improvisation proceeds over repeated form rather than abandoning form;
- one foreground leader/soloist is the default when a soloist is designated;
- comping/support players yield foreground space to the active leader;
- bass and drums preserve rhythmic/form orientation rather than competing for
  foreground by default;
- phrase endings and form boundaries are natural handoff/cue opportunities;
- written head material is treated as the head when available, including a
  conventional head-in/head-out default;
- trading, simultaneous foreground, unusual solo order, special intros/endings,
  metric changes, stop-time, tags, vamps, and arranged figures require explicit
  score/session evidence or a deliberate runtime instruction.

These are defaults, not immutable laws. A chart, conductor/user cue, or explicit
arrangement has higher authority.

## What this rule does not mean

Jam-session default does not mean:

- fixed literal solo order;
- fixed number of solo choruses;
- everybody must solo;
- automatic four-bar trading;
- automatic two-/four-bar intro;
- one canonical ending;
- precomposed solos.

Those details vary between sessions and must come from explicit context rather
than being invented by the system.

## Runtime relationship

The Shared interaction scheduler already expresses many jam-session behaviors:
designated foreground roles lead, comping/support yields to a strong leader,
bass locks the floor, drums support/setup, and form boundaries invite cues.

The convention contract makes that implicit behavior explicit and exposes one
shared default to all players.

Canonical rule:

```text
If genre_family == jazz
and no higher-priority instruction exists:
    performance_convention = JAZZ_JAM_SESSION
```
