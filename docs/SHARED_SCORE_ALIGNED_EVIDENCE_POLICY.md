# Shared Score-Aligned Evidence Policy

## Scope

This policy applies to **all RealSolo instruments and all Legend research**:
Piano, Bass, Drums, Sax, and future players.

Audio time is a source locator. It is not the final musical learning coordinate.

The canonical research flow is:

SOURCE AUDIO
→ DERIVED EVENT / FEATURE
→ SCORE / FORM ALIGNMENT
→ ENSEMBLE / INSTRUMENT ROLE
→ REPEATED POSITION COMPARISON
→ VOCABULARY / TENDENCY / SHARED GRAMMAR

## Canonical musical coordinate

Whenever evidence can be aligned, store:

- song identity
- score source/page where available
- section
- bar
- beat where confidence permits
- chorus index
- performance phase: intro/head/solo/out-head/coda/etc.
- chord / harmonic function when verified
- phrase position
- form/navigation role
- confidence and provenance

A timestamp such as 128.4 seconds remains in AudioScoreAlignment, but comparisons
should be made with MusicalScoreCoordinate.

## Why this is mandatory

The same harmony can mean different things at:
- the head
- first solo chorus
- later solo chorus
- bass/drum foreground
- out-head
- coda

Conversely, two events separated by several minutes can be the **same musical
position** and therefore form the most valuable comparison pair.

This allows questions such as:

- How does Bass realize A1 bar 5 across choruses?
- How does Piano density change at the same ii–V–I?
- Does Drums mark the same boundary differently on head vs solo?
- Does Sax reuse or transform a motif at the same harmonic function?
- Which behaviors survive across recordings at the same score position?

## Evidence levels

### Unaligned
Useful only as navigation / anomaly detection.

Examples:
- high onset density at 3:42
- spectral brightening
- low-band energy increase

Do not promote these directly to musical policy.

### Section-aligned
May support broad role comparison.

### Bar-aligned
May support form/harmony-position comparison.

### Beat-aligned
May support microtiming, accent, entrance, duration, and detailed vocabulary
comparison when source evidence is strong enough.

## Instrument attribution

Whole-mix evidence remains ensemble evidence until the responsible instrument is
verified.

Do not convert:
"onset density increased"
into:
"drums became denser"

without sufficient attribution evidence.

## Cross-chorus and cross-recording learning

The preferred comparison unit is:

same musical position × different chorus/context/recording

rather than:

nearby timestamps in one recording.

This is the basis for separating:
- tune/form requirements
- ensemble-context choices
- player-specific tendencies
- generic style grammar
- one-off performance events

## Runtime boundary

Score-aligned research evidence may bias runtime candidates after promotion, but
it does not precompose future phrases.

Runtime remains:

Perceive
→ Resolve current musical position
→ Generate immediate candidates
→ Evaluate with learned evidence
→ Commit one event
→ Listen again


## Form-relative fallback

A full score is preferred but is not required for useful musical alignment.

When the recurring form length is known, research may use:

- form_length_bars
- form_bar
- chorus/recurrence index
- performance phase
- arrangement segment
- distance to section/form boundary

This is especially important for drums, where knowing "32-bar form, chorus 3,
bar 29" can already support coherent setup, restraint, release and re-entry.

Form-relative alignment is not permission to force every moment into the loop.
Rubato intros, interludes, vamps, tags, codas, outros, cadenzas and special
arranged inserts should be marked outside the core form until their navigation
relationship is verified.

The hierarchy is therefore:

beat-aligned score evidence
> bar-aligned score evidence
> section-aligned evidence
> form-relative evidence
> unaligned timestamp navigation.


## Canonical coordinate contract

Project-wide convention:

- absolute time is provenance and source lookup
- musical structure is the canonical learning/comparison/inference coordinate

Preferred canonical fields, when known:

- form / core-form identity
- section
- chorus / recurrence index
- section_bar
- form_bar
- beat
- subdivision
- phrase_position
- harmonic_position
- cadence_position
- role
- motif_state
- ensemble_state

Example:

form = AABA
section = B
chorus = 2
section_bar = 5
form_bar = 21
beat = 3
subdivision = 0.666...

Audio provenance remains alongside it:

onset_sec = 83.417
offset_sec = 83.962

Rubato, fermata, free-time, pickup, meter/feel changes, interludes, vamps, tags,
codas and special arrangements are not discarded. Their absolute time remains
preserved while musical position is represented through arrangement_segment,
performance_phase, navigation_state and verified form coordinates where
available.

Final-learning rule:

audio timestamp
→ beat grid
→ bar
→ section
→ chorus
→ form position
→ musical/ensemble interpretation

Temporary coordinates such as bar estimates are navigation evidence until
promoted through this chain.
