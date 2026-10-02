# Bebop Restraint Calibration

This pass was introduced after comparing a RealSolo bebop trio render with the
uploaded Charlie Parker reference compilation at the level of broad drummer
behavior. The comparison is treated as a calibration hypothesis, not as
drummer-identification evidence.

## Changes

### Comping
- new snare statements are less eager
- immediate repetition is penalized more strongly
- deliberate space is rewarded sooner
- RETURN and DISPLACED_RETURN become stronger after space

### Bass drum
Bebop no longer accepts the generic medium-strength `bass_drum_comp`
candidate. The runtime separates:
- quiet `bass_floor_support`
- foreground `bass_bomb` / explicit ensemble kick

This avoids an ambiguous middle layer in which the kick is neither felt as a
floor nor heard as a meaningful accent.

### Ride
Quarter-note continuity remains the deep time reference.
Skip-note omission is more attractive while LISTEN / COAST / COME_DOWN.
The previous `accent_skip` option has been removed; phrase energy is expressed
through quarter weight, omission/return, orchestration, or comping rather than
making the skip note a routine accent.

### Chorus-scale self-restraint
`BebopChorusMemory` stores only drummer-local execution history:
- recent_8bar_density
- bars_since_major_statement
- climax_already_supported
- need_to_back_off
- next_form_boundary_distance_bars

It does not redefine Shared Core form. It answers a narrower drummer question:
"Have I already said enough over the recent form span?"

High recent density can reward SPACE and penalize another COMP/SETUP/ACCENT.
After a climax has already been supported, another accent is less attractive.
Approaching a known form boundary can increase setup value while preserving
headroom before it.

## Runtime invariant

No future fill, comping phrase, or ride pattern is frozen.

Shared form / ensemble evidence
→ drummer local history
→ immediate candidate ranking
→ commit one gesture
→ listen
→ re-plan
