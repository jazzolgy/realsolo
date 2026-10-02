# Jazz Harmony Research Program — Shared Core

## Goal

Build instrument-neutral jazz harmonic intelligence that can serve sax/line generation, piano voicing/comping, bass, arranging, transcription, and live ensemble interpretation.

The target is not a chord-scale dictionary. The target is contextual harmonic reasoning under uncertainty and in motion.

## Research order

### 1. Harmonic evidence separation
Preserve Expected / Observed / Inferred Harmony independently. Establish confidence and provenance for each stream.

### 2. Functional context and tonicization
Model tonic, predominant, dominant, secondary dominant, backdoor motion, tritone-sub family, modal centers, temporary tonicization, chromatic approach harmony, and cadence state as context rather than immutable labels.

### 3. Voice-leading intelligence
Represent guide-tone motion, common tones, semitone attraction, contrary/oblique motion, structural bass relation, top-line continuity, and resolution debt. Voice-leading must be usable by both melodic and polyphonic players.

### 4. Tension and colour affordances
Model natural/altered tensions as contextual affordances. Avoid one-scale-per-chord rules. Track whether chord identity has been established, whether a colour is exposed, and whether it has an audible route to a target.

### 5. Harmonic rhythm and future awareness
Use known future harmony to support anticipation and long-range targeting while keeping note-level decisions open until commitment.

### 6. Substitution and reharmonization
Represent substitutions through audible continuity: common tone, guide-tone path, bass logic, target preservation, or narrative function. A substitution with no continuity mechanism is not automatically valid.

### 7. Modal / non-functional harmony
Separate functional tonal reasoning from modal, pedal, planing, static-colour, symmetric and post-bop contexts so the system does not force ii-V-I logic everywhere.

### 8. Ensemble-observed harmony
When comping/bass/soloist evidence differs from the chart, keep the chart as Expected Harmony and update Observed/Inferred Harmony rather than overwriting history.

### 9. Cross-style / cross-legend comparison
Distinguish shared jazz harmony from era, school, instrument and LegendProfile preferences. Parker, Bill Evans, Herbie Hancock, etc. may weight the same harmonic possibilities differently.

## Division of responsibility

Shared Core owns harmonic meaning, affordances, voice-leading semantics, tension/return logic, substitution relations and uncertainty.

player/piano owns piano-specific realization: hand distribution, physical feasibility, register, spacing style, touch, pedal and voicing vocabulary.

Therefore piano voicing research can proceed in parallel, but it should consume this shared harmonic state rather than become a separate theory engine.

## Runtime invariant

Harmony may prepare intentions, target roles and candidate families, but never an exact future line or fixed future voicing sequence.

Perceive -> HarmonicFrame -> affordances -> candidate generation/evaluation -> commit one immediate action -> listen/re-plan.
