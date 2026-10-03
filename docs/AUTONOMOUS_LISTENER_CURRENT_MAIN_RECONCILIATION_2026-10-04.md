# Autonomous Research Listener — current-main reconciliation

The listener has been ported as a consumer of current Shared Core rather than
bringing its older duplicate learning/form stack with it.

## Ownership

The listener owns:

- provider search metadata and source ranking;
- visible official embed playback;
- browser-authorized audio capture;
- resumable queue/checkpoint state;
- realtime acoustic descriptors;
- uncertain instrument/role detector evidence;
- optional source separation / learned model adapters.

It does not own:

- a second canonical form coordinate;
- a second learning coordinate;
- a second Audio Evidence engine;
- RealChord harmony truth;
- Player musical policy.

## Position boundary

Transient detector estimates are allowed, but persistence uses only:

    MusicalScoreCoordinate

through the current-main listener adapter. If bar/beat/form alignment is not
known, the audio evidence remains unaligned. It is not filled with fake zeros or
guessed bars.

The evidence pipeline is therefore:

    provider metadata
      -> visible embed playback
      -> user-authorized PCM capture
      -> DetectorEvidence
      -> ContextCorrection
      -> PerformanceEvidence
      -> optional MusicalScoreCoordinate alignment
      -> Shared learning

Audio timestamp remains source provenance/navigation only.

## Harmony and RealChord

Source discovery metadata is never musical evidence. Once a source is aligned
to a repertoire identity, RealChord may supply Expected Harmony through the
canonical corpus module. Observed and Inferred Harmony remain separate.

## Safety / rights boundary

The listener does not download YouTube media bytes. The server only queries
ordinary metadata; playback occurs in a visible embed. Audio analysis requires
the browser capture permission path. Raw provider media is not written as a
corpus file by this listener.

## Migration from #51

The useful source-selection, checkpoint, detector, model-adapter, separation and
web-controller pieces were ported. The older MetricFormPosition/FormMap and
SharedFormIntelligence ownership from #51 were intentionally not ported as
canonical Shared types. They are superseded by the current-main
MusicalScoreCoordinate contract and listener adapter.
