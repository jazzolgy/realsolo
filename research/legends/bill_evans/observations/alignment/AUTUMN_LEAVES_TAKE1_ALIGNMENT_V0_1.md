# Bill Evans — Autumn Leaves Take 1 Alignment v0.1

## Goal

Create a take-specific bridge:

```
audio timestamp
-> chorus / bar
-> lead-sheet harmony
-> ensemble-role evidence
-> later vocabulary extraction
```

This is the first step toward a Bill Evans Legend Intelligence layer. It is not yet a
Bill Evans solo generator.

## Project sources

`master_index.xlsx` maps Autumn Leaves to:

- NewReal1 p.12
- Realbk1 p.36

The NewReal1 page is used as the primary clean form/harmony reference.

Important score evidence:

- Medium Swing
- 32-bar A-A-B-C form
- editorial note: melody is freely interpreted rhythmically

No full melody transcription is stored in this research record.

## Recording identity

The uploaded compilation places the track at 11:48–17:49, approximately 6:01.

Public discography identifies the 6:01 Portrait in Jazz version as the stereo album
take context. Take identity remains explicitly stored because alternate mono/take
versions have different solo distributions.

## Audio-only alignment

Chroma recurrence analysis produces a strongest recurring harmonic period around
37.1 seconds.

A 32-bar lead-sheet harmonic template fit gives approximately:

- first full form start: 11.98 s
- bar duration: 1.163 s
- chorus duration: 37.216 s
- implied quarter-note tempo: ~206 BPM

This is consistent with a fast swing performance despite slower half-time beat-tracker
estimates around 103 BPM.

## Form grid

Approximate chorus boundaries:

- Chorus 1: 0:11.98 – 0:49.20
- Chorus 2: 0:49.20 – 1:26.41
- Chorus 3: 1:26.41 – 2:03.63
- Chorus 4: 2:03.63 – 2:40.84
- Chorus 5: 2:40.84 – 3:18.06
- Chorus 6: 3:18.06 – 3:55.28
- Chorus 7: 3:55.28 – 4:32.49
- Chorus 8: 4:32.49 – 5:09.71
- Chorus 9: 5:09.71 – 5:46.92

The remaining ending/tag occupies the final ~14 seconds.

These are audio-derived grid candidates, not manually certified downbeats.

## Piano-solo anchor

A public Take-1 transcription study states that the piano solo begins at 2:00.

On the audio-derived form grid, 2:00 falls around:

- Chorus 3
- bar 29

This is musically significant.

Rather than forcing "piano solo starts exactly at a new chorus", the alignment suggests
a late-C-section break/pickup out of the bass foreground leading into the next full
chorus.

Working interpretation:

```
bass foreground
-> late-form piano entry / break
-> full piano-solo chorus
```

This is exactly the kind of ensemble/form interaction RealSolo must retain.

## Take-specific evidence warning

Do not merge all published Autumn Leaves analyses.

Different available sources discuss:
- stereo Take 1 / album version;
- mono alternate take / Take 9.

The well-documented mono take has its own solo distribution and should be a separate
recording_id.

Therefore:

```
same tune + same artist != same arrangement evidence
```

Every extracted Evans vocabulary item must carry:

- recording_id
- timestamp
- chorus
- bar
- take/version provenance

## Implementation consequence

Future vocabulary extraction can now ask questions at an actual musical location.

Examples:

```
What does Evans do at:
  chorus 4 bar 1 over Cm7?

How does LH comping change:
  bass foreground -> piano foreground?

How does a phrase approach:
  bar 8 -> bar 9?
  bar 16 -> bar 17?
  bar 24 -> bar 25?
  bar 32 -> next chorus?
```

This is more useful than aggregate statistics such as "Evans uses many ninths".

## Next extraction unit

Start with:

1. late Chorus 3 bars 29-32 — piano entry / handoff;
2. Chorus 4 bars 1-8 — first full piano-solo A section;
3. Chorus 4 bars 9-16 — repeated A with development;
4. Chorus 4 bars 17-24 — B-section contrast;
5. Chorus 4 bars 25-32 — cadence / continuation into next chorus.

For each unit extract only evidence that can later become executable:

- phrase entrance
- rhythmic placement
- target function
- motif identity / transformation
- interval-motion class
- tension/release
- register trajectory
- LH texture
- RH-LH timing relation
- bass/drum interaction
- phrase ending / continuation

Exact note sequences are not promoted into public generic policy.
