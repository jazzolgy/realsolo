# RealSolo Product Stages

## Stage 1 — Chart + Playback (no microphone required)

The first usable product is a complete practice/performance app even before interactive listening is enabled.

The user selects a song/chart and sees:
- chord symbols
- form / sections
- current bar and beat
- tempo and meter
- playback position

The app then provides one of two musical roles:

### Accompaniment mode
The user plays the solo / melody and RealSolo provides accompaniment.

Typical case:
- saxophone / trumpet / vocal / guitar soloist
- RealSolo: piano/bass/drums or another configured backing ensemble

### Soloist mode
The user provides accompaniment/comping and RealSolo provides the solo line.

Typical case:
- pianist practicing comping
- RealSolo: AI soloist
- user: piano comping

Stage 1 does not require microphone analysis. Musical timing comes from the chart
transport itself.

## Stage 2 — Interactive Ensemble

Stage 2 adds microphone-first perception.

The chart transport becomes an expectation prior, not an absolute clock.
The live performer can:
- push or lay back
- stretch a phrase
- use pickup notes
- pause
- cue an ending
- change energy
- hand off musical space

Audio perception updates the current ensemble state, and the system may revise
uncommitted musical intentions.

## Architectural rule

Stage 2 extends Stage 1. It must not replace it with a separate app architecture.

```
SongChart
  -> ChartTransport
  -> Expected Harmony / Form / Beat
  -> Music Intelligence Core
  -> AI role: accompaniment or solo
  -> Performance Output

                      + microphone perception (Stage 2)
                      -> Observed performer evidence
                      -> EnsembleState
                      -> re-plan
```

MIDI remains optional. It is useful for digital-instrument users and development
ground truth, but it is not a required product input.
