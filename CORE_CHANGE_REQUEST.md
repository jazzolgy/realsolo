# Core Change Requests

## Stage-1 chart-aware candidate generation

### Requested core change
Add a shared Core interface that generates immediate candidate families from
expected harmony/form/phrase state, rather than keeping chart-tone candidate
generation inside the realtime workstream.

### Musical reason
Stage 1 now supports an AI soloist that must make one note-level commitment at a
time from chart context. The current `Stage1Soloist` adapter intentionally uses
the shared `OnlineMusicalEvaluator` and `perform_one_event()` contract, but its
candidate construction is only a temporary integration baseline.

### Affected modules
- shared harmony representation
- phrase/intention planning
- online candidate generation/evaluation
- instrument grammar adapters

### Regression risk
A Core-owned generator must not freeze exact future note sequences or bypass
current ensemble evidence.

### Tests required
- one event committed per decision
- exact future note sequence remains prohibited
- next harmony can influence candidate families without scripting a phrase
- instrument grammar remains separate from shared harmony/phrase reasoning
