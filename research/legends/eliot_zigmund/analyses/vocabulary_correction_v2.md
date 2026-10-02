# Zigmund vocabulary robustness correction

The initial `Without a Song` pass promoted three IOI cells too quickly:
`2-3-1`, `1-3-2`, and `3-1-2`.

A second robustness pass changed detector threshold and grid estimation across
12 settings and compared matched 25-second windows from five Eliot Zigmund
performances in the supplied Bill Evans compilation.

Result: the three cells are low-frequency and detector-sensitive. They do occur,
but not robustly enough to justify current **legend vocabulary** status.

The much more stable cells are simple `1-1-1`, `1-1-2`, and `2-1-1`
families. Those are too generic to call "Zigmund language" from full-mix onset
analysis alone.

Therefore:
- keep the original three cells as provisional research observations;
- remove them from the active Shared Legend runtime index;
- do not create replacement Zigmund signature cells yet;
- require either manually verified drum transcription, source-separated drum
  evidence, or recurrence in an independent recording before promotion.

This correction is intentional: source-grounded Legend Intelligence must prefer
false negatives over confidently encoding detector artifacts.
