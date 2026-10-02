# Along Came Betty — Restraint Calibration Baseline

This baseline is derived from the user-provided RealSolo trio render. The raw
audio is not stored in the repository.

Measured whole-mix values:
- duration: 59.878 s
- tempo periodicity detected: 73.828 BPM
- musically interpreted double-time pulse: 147.656 BPM
- detected transient/onset count: 398
- onset activity: 6.647 events/s
- median RMS: -15.797 dBFS
- 90th-percentile RMS: -13.248 dBFS

These are **whole-mix** measurements. They do not claim that every onset is a
drum hit, and they should not be used as direct historical-style truth.

## A/B target

After the restraint calibration, re-render the same arrangement and compare:
- whole-mix onset activity
- snare statement count
- mean/median gap between snare statements
- RETURN / DISPLACED_RETURN share
- intentional non-response share
- quiet floor-kick vs bomb count
- skip-note omission rate
- active-gesture density over rolling 8-bar windows
- form-boundary setup rate

The desired change is not simply "lower density everywhere." The target is:
**less redundant commentary, longer conversational spacing, clearer bass-drum
roles, preserved ride continuity, and stronger phrase/form narrative.**
