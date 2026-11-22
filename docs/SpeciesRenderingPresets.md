# Reusable species rendering presets

Eight source-linked illustrative presets are available in `PhysicalRendererTest/index.html`. They are a first reference-guided implementation, not trained phenotypes or expert-approved identification illustrations. None is connected to venom input. The remaining catalog labels have not been converted into rendering presets.

## Presets

| Source label | Illustrated variant and distinguishing features |
| --- | --- |
| Naja kaouthia | Brown expanded-hood cobra; single rear monocle; flattened front three-quarter head. |
| Naja naja | Brown expanded-hood cobra; paired spectacle loops and connecting band. |
| Oxyuranus scutellatus | Brown robust body, slender neck, deeper head and paler snout. |
| Dendroaspis polylepis | Slender grey-olive closed-mouth form; elongated head; no broad cobra hood. |
| Crotalus atrox | Heavy trunk, broad head, keeled scales, pale-bordered diamonds, tail bands and segmented rattle. |
| Bitis gabonica | Heavy body, broad head, keeled scales and geometric leaf-litter pigment blocks. Historical taxonomy and reference identities need further review; large nasal horns are not assigned. |
| Dispholidus typus | Green adult male-style variant, slender trunk, large eye, dark-edged keeled scales and long tail. |
| Aipysurus laevis | Olive-brown mottled variant, smooth scales and a broadened paddle shown in broadside projection. |

Shared open S poses are presentation choices. A fixed pose does not establish biological posture or proportions. Dorsal/oblique and ventral views are simplified 2D surface studies, not camera projections of a 3D animal. A sea-snake paddle's broadside depiction should not be read as its width in dorsal view. Local photo references were inspected visually, but most retain unreviewed provider identities. No source-photo decisions or injury exclusions were changed. Preserved/damaged specimens were not used to fit anatomy.

## Source of truth

`config/species_presets/*.json` contains one independently editable preset per source species label. Identity uses the existing catalog `species_id`; similar names are not merged. Each preset separates:

- Source label, common name, variant and validation status.
- References to the physical profile, original sources and specific candidate photo IDs/hashes.
- Explicit unresolved description fields.
- Artistic parameters for body build, head type, palette, surface texture, pigment family, tail and shared presentation pose.
- Unpopulated biological measurements and venom mappings (`null`).

The palette hex values, numerical widths, eye radii, scale pitch and pattern spacing are authored drawing values. They are not species measurements, population distributions, anatomical scale counts or inferred venom effects. Head-shield paths are illustrative, not an expert-reviewed map of diagnostic shields. Biological facts must not be added by copying a related species' numeric preset.

The four original starter references are in `docs/StarterSpeciesPhysicalProfiles.md`. Additional Gaboon viper, boomslang and olive sea snake sources are recorded in the respective JSON files. Taxonomic caveats remain visible in the editor. Reference photographs belong to different individuals from the venom measurements.

## Build and run

From the repository root:

```sh
python3 scripts/build_species_presets.py
node PhysicalRendererTest/species-presets.test.cjs
node PhysicalRendererTest/build-preview-gallery.cjs
```

The Python builder validates catalog identity and photo-reference hashes/status, and emits the JSON snapshot plus an offline-compatible JS bundle in `PhysicalRendererTest/presets/`. The browser reads the JS bundle so opening the interface directly with `file://` does not require fetching JSON. Do not edit generated bundle files manually.

Open `PhysicalRendererTest/index.html`. The selector switches species; unsupported controls are disabled. Edits are retained per species during the current page session, with Reset affecting only the active species. The monocled cobra's original generated illustration remains a comparison option only for that species. All active models use SVG geometry without embedded raster images.

Export an SVG for the current view. Export preset settings to save artistic overrides and the source identity as JSON. Load saved settings validates the identity, supported views, colors and numerical limits before applying them. This saves settings, not new biological evidence. Edited settings do not silently become catalog defaults.

## Code organization

- `anatomy.js`: established cobra geometry and head views, preserved from the prior renderer.
- `species-geometry.js`: dispatches by body plan; generates other head/body/tail shapes using shared geometric primitives.
- `species-renderer.js`: pure deterministic SVG generation, scale surface coordinates, pigment, keel strokes, ventral plates, head details and appendages.
- `species-editor.js`: selector, controls, state, export and load behavior.
- `preset-settings.js`: strict saved-setting validation.

Renderer branches use anatomical feature/pattern enums, not species names. Distinct scale palettes are evaluated along the curved body surface. Rattle count is an artistic parameter, never an age estimate. Defaults describe one coherent illustrated variant; they do not combine all documented sex, age or locality alternatives.

## Verification and remaining limits

Automated tests cover 144 preset/view/shape combinations, outline closure and intersections, deterministic vector output, color/geometry independence, species-specific marking/appendage isolation, unchanged preset evidence, and settings round-trip/rejection cases. All eight generated SVGs parse as XML. These checks establish implementation properties, not scientific accuracy.

Browser checks cover all eight selections, feature visibility, disabled controls, detail/full views, reset and retention of edits across species switching. Saved-settings validation is tested directly; native file-picker and download completion are not automated. The comparison gallery allows visual review of all eight drafts.

## Anatomical remodeling, revision 2

The eight presets now use individually authored skull/landmark and body-taper data, plus separate cobra hood profiles. See [SpeciesRemodelingReview.md](SpeciesRemodelingReview.md) for photo-to-feature notes, before/after review and the workflow for further species. `head-renderer.js` constructs skull details from each preset; `species-geometry.js` joins the authored head to its swept trunk. The editor includes a silhouette mode, and the review gallery includes head comparisons and attributed original references.
