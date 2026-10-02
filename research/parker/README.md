# Charlie Parker Research Corpus

Canonical home for Charlie Parker-derived research in RealSolo.

## Purpose

Use Parker sources to learn conditional musical behavior, phrase grammar, timing/space,
ensemble interaction, and style tendencies. Do not store or schedule literal future
Parker phrases as runtime output.

## Canonical research artifacts

### Uploaded-audio studies
- PARKER_GREATEST_HITS_AUDIO_STUDY_V0_1.md
- parker_greatest_hits_audio_annotations_v0_1.json

These are grounded in the private uploaded Charlie Parker compilation. The raw audio is
not committed to the public repository.

### Instrument-transfer studies
- PARKER_TO_PIANO_SOLO_TRANSFER_V0_1.md
- PARKER_DRUMS_AUDIO_STUDY_V0_1.md
- PARKER_DRUMS_DEEP_STUDY_V0_1.md

These documents record instrument-specific interpretation of Parker-derived evidence.
They are research evidence, not runtime ownership. Actual musical policy remains under
players/<instrument>/.

## Parker-derived Shared Core/runtime locations

The following stay in their functional locations because they are imported or tested there:

### Shared Bebop Core
- src/music_intelligence/bebop/parker_conditional_statistics.py
- src/music_intelligence/bebop/parker_online_profile.py
- src/music_intelligence/bebop/parker_phrase_space_profile.py
- src/music_intelligence/bebop/parker_statistical_profile.py
- src/music_intelligence/bebop/parker_v131_blend.py
- src/music_intelligence/bebop/parker_v132_blend.py

### Derived data
- src/music_intelligence/bebop/data/parker_symbolic_conditional_stats_v131.json
- src/music_intelligence/bebop/data/parker_phrase_space_stats_v132.json
- src/music_intelligence/bebop/data/parker_recording_alignment_benchmarks_v133.json

### Architecture / audit records
- docs/UMR_v1.31_PARKER_CONDITIONAL_ONLINE_PRIORS.md
- docs/UMR_v1.32_PARKER_PHRASE_SPACE_AND_ALIGNMENT_AUDIT.md

### Regression tests
- tests/test_v131_parker_conditional_statistics.py
- tests/test_v132_parker_phrase_space.py

## Player-side Parker-derived behavior

Some player code legitimately contains Parker-derived abstractions, but the code remains
owned by the player package. Research evidence belongs here; executable policy belongs
under players/.

## Source handling

Raw copyrighted/private source audio, books, and transcriptions are not copied into the
public repository. Store provenance and aggregate/derived research only.

## Runtime invariant

Perceive -> generate immediate candidates -> evaluate -> commit one event -> listen again

Parker evidence may bias an immediate decision, but it must not become a precomposed
future solo.
