# Freddie Hubbard Comping Transcription Study v0.1

Source: *Jazz Piano Voicings — Transcribed Comping from Volume 60 Freddie Hubbard*
(Dan Haerle / Mark Levine, Jamey Aebersold Jazz).

This study uses selected transcription pages as observational performance evidence.
It does **not** treat any literal voicing or rhythmic cell as a phrase template to memorize.

Selected comparison set:
- Mark Levine — Little Sunflower
- Dan Haerle — Gibraltar
- Dan Haerle — Crisis

## Evidence policy

- TRANSCRIPTION-OBSERVED: directly visible in the notation.
- DESIGN-INFERENCE: RealSolo abstraction motivated by the transcription.
- OPEN: requires audio, expert review, or larger sample before stabilization.

## 1. Little Sunflower

### TRANSCRIPTION-OBSERVED

The opening is a long D-minor/modal field with repeated returns to the same harmonic area.

Across the same harmonic field the piano does not use one fixed realization:
- sustained two-hand sonorities;
- short offbeat chord attacks;
- repeated rhythmic cells;
- rests between gestures;
- denser chordal activity later in the excerpt;
- register and voicing-size changes across the chorus.

The pages therefore show that constant harmony does not imply constant piano action.

Later measures show noticeably more repeated block-like activity and thicker voicings,
while earlier passages contain more space and mixed sustain/punctuation.

### DESIGN-INFERENCE

Useful state dimensions:
- static_harmony_duration
- local_pattern_consistency
- local_texture_density
- local_sustain_ratio
- local_register_center
- phrase_section_energy

A static harmonic field can still support a developing accompaniment narrative.

## 2. Gibraltar

### TRANSCRIPTION-OBSERVED

The opening/head repeatedly alternates G minor and C7 at a fast tempo.

The piano uses highly recognizable recurring rhythmic placements across repeated
harmonic cycles. The pattern is not mechanically identical in every measure, but a
stable comping identity is clearly maintained across several cycles.

Later passages move among:
- sparse attacks;
- held sonorities;
- repeated short chord patterns;
- denser block-chord textures;
- occasional longer rests.

The same Gm-C7 harmonic environment therefore supports both consistency and variation.

### DESIGN-INFERENCE

This is strong evidence that RealSolo needs two independent controls:

- variation pressure;
- pattern consistency strength.

A model that always penalizes high similarity will destroy legitimate groove identity.
A model that always rewards repetition will become mechanical.

Pattern identity should be able to persist while:
- voicing changes;
- register changes;
- dynamics/touch change;
- one attack is omitted;
- a response window interrupts the pattern.

## 3. Crisis

### TRANSCRIPTION-OBSERVED

Compared with Gibraltar, the harmony changes more frequently and the accompaniment
shows less reliance on one recurring rhythmic cell.

Visible behaviors include:
- sustained or half-note-like harmonic support;
- short chord punctuation;
- rests;
- compact and wider sonorities;
- chromatic/linear movement between harmonic events;
- texture changes around formal boundaries and bridge material.

The transcription suggests stronger coupling between harmonic/form change and
accompaniment texture than in the repeated-vamp case.

### DESIGN-INFERENCE

Useful distinction:
- pattern-driven continuity for stable/vamp harmony;
- harmony/form-driven texture change for faster-moving harmonic contexts.

This does not mean fast harmonic rhythm forbids groove repetition. It means the policy
should not use the same pattern-consistency prior regardless of harmonic/form context.

## 4. Cross-piece findings

### 4.1 Same harmony, different action

Repeated harmony can produce:
- silence;
- sustain;
- punctuation;
- repeated groove cell;
- denser block texture.

This supports the existing RealSolo principle:

Harmony != Piano Action

### 4.2 Repetition is contextual

The transcriptions contradict a universal anti-repetition rule.

Observed repetition may function as:
- groove identity;
- formal continuity;
- energy stabilization;
- an accompaniment bed.

Therefore:
- exact mechanical repetition may still receive pressure to vary;
- local pattern consistency may partially relieve that pressure;
- variation can occur in dimensions other than rhythm.

### 4.3 Texture evolves over phrase/section time

Across the selected pages, voicing size, sustain, attack rate, and register do not stay
constant across a chorus.

RealSolo should eventually model texture trajectory as a short-term state rather than
only evaluate isolated events.

### 4.4 Harmonic rhythm should influence continuity policy

A long vamp can sustain a recognizable rhythmic comping identity.

More rapidly changing harmony may require greater sensitivity to:
- voice leading;
- harmonic arrivals;
- form boundaries;
- register/texture reset.

This is a policy tendency, not a deterministic rule.

## 5. Implementation consequence

Added experimental field:

pattern_consistency_strength

It is separate from:
- variation_pressure;
- groove_lock_strength;
- motif_continuity_strength.

Current behavior:
- high pattern consistency reduces, but does not erase, exact-repeat penalty;
- highly similar sounding gestures may receive a small consistency reward;
- silence repetition remains handled separately;
- no future pattern sequence is precomposed.

## 6. Next extraction targets

The transcription volume should next be expanded with at least:
- one ballad/slow piece;
- one medium swing or blues;
- one additional fast or modal piece;
- one Mark Levine and one Dan Haerle example in comparable harmonic conditions.

For each, annotate:
- harmonic stability / rate of change;
- attack density;
- silence spans;
- sustain ratio;
- voicing size;
- register center/span;
- repeated rhythmic cell identity;
- pattern persistence length;
- section/form boundaries;
- density trajectory.

Exact numerical transcription should be added only after a reliable symbolic/manual
annotation workflow is established.
