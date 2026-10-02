# Three-Level Audio Test Profiles

RealSolo provides three sample-density profiles so rendering quality can be
A/B/C tested without changing any musical Player logic.

## Full

Reference-quality developer evaluation.

- complete Karoryfer Meatbass release
- complete Virtuosity Drums release
- roughly 1.5 GB of source downloads for the current bass + drum set

```bash
realsolo-ensemble install-assets --profile full
realsolo-ensemble stage1 --asset-profile full
```

## Lite

External musician / beta testing.

- selected source samples total roughly 27 MB
- bass: 8 pitch anchors x 2 velocity layers x 2 round robins
- ride: 3 velocity layers x 2 round robins
- closed hi-hat: 4 velocity layers x 2 round robins
- kick: 4 velocity layers x 2 round robins
- snare: 4 representative dynamics

```bash
realsolo-ensemble install-assets --profile lite
realsolo-ensemble stage1 --asset-profile lite
```

## Mini

Fast installation, smoke tests, UI/timing checks.

- bass: 4 pitch anchors x 1 velocity layer x 1 round robin
- ride / closed hi-hat / kick / snare: one representative sample each
- expected source material is only a few MB

```bash
realsolo-ensemble install-assets --profile mini
realsolo-ensemble stage1 --asset-profile mini
```

Installed profiles coexist. Switch without reinstalling:

```bash
realsolo-ensemble use-assets --profile full
realsolo-ensemble use-assets --profile lite
realsolo-ensemble use-assets --profile mini
```

The active profile is copied to `realsolo_manifest.json`, which the browser
renderer already consumes. The same RenderGesture stream is used in all three
profiles; only sample density changes.
