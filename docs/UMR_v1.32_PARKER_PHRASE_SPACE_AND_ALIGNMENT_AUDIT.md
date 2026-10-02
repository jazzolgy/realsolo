# UMR v1.32 - Parker Phrase Space + Alignment Audit

## Why this pass

v1.31 converted symbolic interval behavior into bounded online motion priors. The next step was supposed to move toward real Parker performance evidence. Before trusting any external aligned derivative, the alignment methodology was audited.

## Public aligned-Omnibook research

Riley and Dixon's 2024 work provides an enhanced Charlie Parker score-audio dataset with MusicXML, downbeats and performance-aligned MIDI. This is exactly the evidence class needed for note-onset, duration and microtiming study.

A separate public analysis repository, code91/parker-timeseries, publishes derived CSVs from that corpus. Its phrase-detection pass extracts rests from MusicXML and uses rests >= 0.5 quarter note as phrase boundaries.

That score-level phrase-space evidence is useful and was promoted into v1.32.

## Phrase-space result

Across 46 tunes, 1,461 phrase-boundary rests were analyzed:

- 0.5 quarter: 548 / 37.51%
- 1 quarter: 643 / 44.01%
- 2 quarters: 237 / 16.22%
- 4 quarters: 31 / 2.12%

Therefore 62.35% of boundaries contain at least one full beat of space, and 18.34% contain at least two beats.

This strongly supports the project principle that silence is active musical structure rather than a failure to generate notes.

## Important tune variation

The distribution is not explained by tempo alone. In the derived score data, Ko Ko has much more two-beat and four-beat space than Confirmation despite both being fast bebop repertory. Runtime therefore must not collapse phrase-space choice to a simple BPM rule.

## Alignment audit

The public parker-timeseries CSV named timestamps must NOT be used as performance-microtiming evidence.

Its alignment script converts score measure/beat coordinates into MIDI ticks and then converts those ticks using the MIDI tempo map. It does not read each aligned note-on timestamp and match that note event to the corresponding score note.

That is suitable for coarse harmonic time-series positioning but not for measuring Parker's downbeat delay, upbeat placement, articulation, note duration or swing microtiming.

Accordingly v1.32:
- accepts the derived MusicXML rest statistics as score-level phrase-space evidence;
- rejects the derived timestamp column as a source of microtiming priors;
- retains the requirement to obtain/use the original performance-aligned MIDI or independently align the supplied recordings before updating timing priors.

## Runtime change

A monophonic CandidateEvent with pitch_midi=None is treated as an immediate rest/space candidate. The OnlineMusicalEvaluator derives rest-duration tags at commit time: rest_half_beat, rest_one_beat, rest_two_beats and rest_four_beats_plus.

The Parker phrase-space profile is bounded at lower confidence than recording evidence and is mixed at weight 0.55 in PARKER_V132_BLEND.

The runtime contract remains unchanged:

Perceive -> prepare intention/candidates -> evaluate -> commit one immediate event (note OR rest) -> listen again -> re-plan.

Silence is therefore an action that can be chosen responsively, not a prewritten gap in an offline solo.
