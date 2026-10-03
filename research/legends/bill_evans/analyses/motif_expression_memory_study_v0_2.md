# Bill Evans — Form-Bar Expressive Proxy v0.2

This pass deepens the previous HOW study by storing one observation row for each
form bar of the Autumn Leaves head and first piano-solo chorus.

## What is new

The earlier study operated mainly at 8-bar section resolution.  This pass stores
64 bar-relative observations:

- head bars 1–32
- piano-solo chorus 1 bars 1–32

Each row retains seconds only as source provenance and uses
performance_phase / section / form_bar as the musical address.

Measured proxy dimensions:

- harmonic-component level
- harmonic/percussive body relation
- within-bar dynamic range
- attack-strength proxy
- harmonic spectral centroid

## Same-form-position result

Comparing head and solo at the same form bar:

- mean solo-minus-head harmonic level: about +1.82 dB
- median: about +1.31 dB
- mean centroid shift: about +590 Hz
- mean body-ratio change: about -0.040
- mean attack-strength change: near zero

The important result is the **dissociation**:

the solo becomes brighter / more foreground in the harmonic component without a
parallel global increase in attack strength.

This strengthens the Shared HOW separation:

dynamic_level != accent_strength != note_body != register/brightness.

## Why this matters for motif memory

A returning motif should not retrieve an absolute performance stamp.  The memory
needs to retain motif identity separately from recent HOW history.

A useful runtime question is:

same motif identity
× current form address
× current performance phase
× ensemble density
× recent expression of this motif
→ current expressive realization

That allows a motif to return recognizably while becoming softer, brighter,
longer-bodied, differently accented, or less foreground.

## Evidence gate

This file is OBSERVATION_ONLY.

The audio is a mixed trio recording. HPSS harmonic energy is not isolated Bill
Evans piano, and bar boundaries are interpolated from the existing 8-bar
score-aligned windows. These rows may drive navigation, architecture and
annotation priorities, but they are not direct Bill Evans velocity constants.

Promotion to a Bill Evans expressive tendency requires repeated aligned examples
plus instrument attribution.
