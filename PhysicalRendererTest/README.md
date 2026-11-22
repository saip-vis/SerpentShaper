# SerpentShaper species preset editor

Open `index.html` in a browser and choose a species. The editor currently contains 174 catalog-linked source-label presets, including unreviewed starter scaffolds and reference-informed drafts. This is not a verified count of distinct species. The editor labels unreviewed starters; their colors and shapes can be placeholders. None of these drawings has a validated accuracy score.

Edit the available shape, palette, and pattern controls, and inspect the full-body or detail view. Edits persist per species for the current session. Export SVG artwork or JSON settings; Load saved settings restores validated overrides. No model has been trained and venom inputs are not connected.

The authoritative preset files live in `../config/species_presets/`. From the repository root, rebuild the browser bundle and gallery with:

```sh
python3 scripts/build_species_presets.py
node PhysicalRendererTest/build-preview-gallery.cjs
node PhysicalRendererTest/build-session-gallery.cjs
```

The original pilot photographs and locally cached external reference images are intentionally excluded from Git. Source manifests, attribution, links, and the generated illustrations are included. If local reference images are unavailable, the bundle can still be rebuilt; it reports which external images could not be hash-checked. The gallery links to the cited sources instead of requiring those local photographs.

Run `node PhysicalRendererTest/species-presets.test.cjs` and `node PhysicalRendererTest/refinement-details.test.cjs` to check rendering and geometry. These are software checks, not anatomical validation. See [SpeciesRenderingPresets.md](../docs/SpeciesRenderingPresets.md) and [RefinementSession_2026-11-21.md](../docs/RefinementSession_2026-11-21.md) for evidence and remaining work.
