# Reference-guided anatomical remodeling

Model revision 2 replaces the generic non-cobra skull/body construction. It is a qualitative photo-guided drawing revision, not a morphometric fit, identification model, or expert anatomical validation.

## What changed

Each non-cobra preset now owns a projected skull outline, neck attachment, eye and nostril landmarks, jaw seam, head-scale treatment, and body-width stations. Head and trunk share one continuous closed boundary; a smooth neck lead avoids offset-curve loops at the attachment. Different silhouettes no longer rely on changing a shared outline's global width. The cobras retain their approved head construction and now have individually authored, smoothly blended symmetric hood profiles.

| Preset | Anatomical work |
| --- | --- |
| Black mamba | Long, low skull; modest lateral eye; pale narrow lip; gradual neck transition; long slender trunk before taper. |
| Boomslang | Shorter rounded skull and enlarged eye region; conspicuous lateral eye; stronger neck constriction; earlier tail taper. Green adult-style palette kept separate from structural head close-ups. |
| Coastal taipan | Deep rectangular skull, blunt pale snout, broad labial regions; narrow anterior neck leading into a robust trunk. |
| Western diamondback | Angular posterior jaws, narrow neck, independent eye/nostril/pit landmarks, small head scales; heavy middle trunk and short ringed tail/rattle. |
| Gaboon viper | Broad leaf-shaped skull with small scales; posterior eye region, midrib and cheek pigmentation; heavy trunk and a short, rapid tail taper. No unverified large nasal horns. |
| Olive sea snake | Small blunt head, weak neck constriction and robust trunk; narrow tail peduncle leading into a rounded broadside paddle. |
| Monocled cobra | Approved front skull retained; individual rounded expanded-hood profile; dorsal monocle remains separate from ventral pigmentation. |
| Spectacled cobra | Approved cobra head construction retained; individually broader illustrated display hood; paired spectacle geometry retained. |

The cobra hood differences describe selected illustrative displays, not a universal quantitative difference between species. The shared open pose is retained for comparison, rather than using pose to manufacture apparent species differences. Display scale is shared on review plates; it is not a statement of equal actual adult lengths.

## Evidence trail

Every `config/species_presets/*.json` now has:

- A per-preset `model_revision` (the original remodeling started at revision 2).
- `evidence.reference_feature_map`, associating every candidate photograph with the specific visual information used and its limitations.
- `evidence.modeling_observations`, listing the changes and relevant reference IDs.
- `artistic_parameters.head_geometry` and `body_stations` for non-cobras, or `hood_profile` for cobras.

These drawing coordinates are not species-wide measurements. Mamba reference photographs are oblique/frontal, so lateral head length is also informed by the pre-existing qualitative reference account. Boomslang head close-ups may show a different stage and color from the green preset; they are structural guides rather than a combined specimen. The olive sea snake's poorly resolved endpoint photo does not establish tail dimensions. Large features that are unsupported or uncertain remain unresolved.

The original photo review states and exclusions remain unchanged. Reference review pages copy original JPEGs without modifying them, retain photo IDs, attribution/license labels and source links, and identify them as provider-labelled references. Mirrored reference JPEGs stay ignored by Git and are regenerated from the local collection. The reviewed images are not assumed to depict the animals from the venom composition studies.

## Reviewing the result

Open `PhysicalRendererTest/preset-previews/head-comparison.html` for the black mamba and boomslang, or the comparison index for the current drafts. Each card has full-body and enlarged head models, a head silhouette, observations, an expandable original photo, and before/after outline comparison.

The editor's **Silhouette** checkbox removes pigment and head detail to expose the underlying boundary. It changes only presentation, not anatomy. The **Head detail** view helps assess eye prominence and the head-neck transition. Earlier preset artwork remains under `preset-previews/before-remodel/`.

## Verification

The source builder checks that Bezier segments connect, snout and neck endpoints agree, body stations are finite, tail radius ends at zero, and every reference has a scoped note. Rendering tests currently cover 594 species/view/shape combinations across 33 drafts, outline intersections, vector-only output, deterministic rendering, feature isolation and setting validation.

Additional regression checks compare mamba/boomslang normalized skull area and length, relative eye prominence, and normalized trunk/tail taper. Eye landmarks must fit inside the generated skull boundary. These checks preserve deliberate anatomical distinctions and prevent a future global recolor/resize from collapsing the pair again. They do not establish biological accuracy.

## Workflow for remaining species

1. Select clear healthy head, whole-body and tail references; keep their IDs, review state and provenance. Record missing views.
2. Note which visible features each photo supports, including angle, life stage and color limitations. Use literature to corroborate features; keep unknown measurements explicit.
3. Author the skull and its neck attachment independently. Place eye, nostril, jaw and head shields within that boundary.
4. Author trunk mass distribution and tail transition in a consistent comparison pose. Keep special appendages separate and correctly attached.
5. Review plain silhouettes and enlarged heads before tuning color and pattern.
6. Reapply scales and pigment in anatomical coordinates, checking transitions and surface visibility.
7. Run geometry and source checks, then visually compare against the selected photographs. Record remaining discrepancies for human review.

No species should be considered accurate merely because its outline is different or its tests pass. The next catalog expansion should use this same reference review workflow before being marked ready.


## Catalog expansion checkpoint (2026-11-21)

The full user-requested catalog modeling pass is **unfinished**. There are 174 catalog source labels and 33 editable draft presets (8 existing plus 25 added in this expansion). There are 141 source labels without presets. Of those, 8 have contact-sheet observations and need further references, 1 has a supplemental photograph reviewed but insufficient head detail, and 132 await visual review. A source label is not necessarily a distinct modern taxon.

The current authoritative progress record is `reports/species_modeling_ledger.json`. It records inspected contact sheets, individually opened photographs, observed traits, actual drawing refinements, source checks and unresolved issues. A rendered draft does not mean all anatomical views were available. No catalog-wide completion or expert accuracy claim is made.

Boomslang revision 3 flattens the roof and lower jaw and reduces eye size while retaining its prominent eye. The black mamba's accepted head design is retained. Newly authored groups include the four Agkistrodon species, the two Aspidelaps species, Picado's jumping pitviper, puff/horned/rhinoceros adders, six Bothriechis species, Campbell's toad-headed pitviper, seven Bothrops species, and the vine snake.

The expansion adds band/hourglass/chevron/trapezoid/hook pigment families, dark-edged blotches, reticulation, authored facial pigment and rostral/supraocular/nasal contours. Individual dimensions are artistic design values. The neck attachment now selects a forward body station, preventing a long skull from doubling the neck backward.

Supplemental university photos support the vine-snake head; the Orianne Society's healthy Saint Lucia lancehead photograph replaces damaged local anatomy references. Cached external originals are private reference material, excluded from Git; no training or redistribution rights are inferred. Local photo review decisions and venom data remain unchanged.

Review plates generated from the actual SVGs live in `PhysicalRendererTest/visual-studies/catalog-modeling/`. Regenerate them with `scripts/render_model_review.py` after rebuilding the preview gallery. Original photos are not edited. Shape checks and visual comparisons are separate: passing tests establishes valid geometry, not biological accuracy.

## Catalog starter coverage

All 174 source labels now have selectable editable presets. The latest 131 are explicitly `unreviewed_starter` scaffolds generated by `scripts/create_catalog_starter_presets.py`. Their broad drawing templates are selected by genus, without species-specific photo analysis; colors and markings are neutral placeholders. They are not finished anatomical models and must be visually reviewed and remodeled before an accuracy claim. Their prior contact-sheet observations, when present, remain in the modeling ledger. The ledger retains the `unreviewed_starter` status even though a preset exists. Existing 43 drafts were not replaced.
