# Reference-guided refinement pass — November 21, 2026

This is a work-in-progress record, not a claim that the catalog has passed anatomical validation. The catalog contains 174 **source labels**, each with an editable drawing preset. The number of source labels is not a verified count of distinct species: NCBI lists *Cryptelytrops purpureomaculatus* as a synonym of *Trimeresurus purpureomaculatus*. Both source labels are retained to preserve data provenance.

The per-species source preset under `config/species_presets/` records exact pilot image IDs, how each photo was used, source links, modeling observations and remaining flags. Open `PhysicalRendererTest/preset-previews/index.html` to compare the current SVG model, head, silhouette and cited photo. `reports/species_modeling_ledger.json` is the status inventory. Photo IDs are provider labels and have not been independently authenticated; using a photo here does not approve it for training or change its review state.

## Drafts worked on in this pass

- *Cerastes cerastes*, *Cerastes vipera*, *Cerrophidion godmani*, *Cerrophidion sasai*.
- *Crotalus adamanteus*, *C. basiliscus*, *C. culminatus*, *C. durissus*, *C. horridus*, *C. oreganus*, *C. polystictus*, *C. scutulatus*, *C. simus*, *C. tigris*, *C. tzabcan*, *C. viridis*.
- *Cryptelytrops purpureomaculatus*, *Daboia russelii*, *D. siamensis*, *Deinagkistrodon acutus*, *Dendroaspis angusticeps*, *Echis carinatus*.
- *Hydrophis curtus*, *H. platurus*, *H. schistosus*, *Laticauda colubrina*, *Gloydius brevicaudus*, *Hypnale hypnale*.
- *Naja melanoleuca* and *N. pallida*: initial color, hood, and throat-band work; additional head fitting remains essential.
- *Vipera aspis*, *V. berus*, *V. nikolskii*, *V. renardii*, and *V. ursinii*.
- *Lachesis acrochorda*, *L. melanocephala*, *L. muta*, and *L. stenophrys*.

Each listed preset has an initial visual comparison; most also received a follow-up adjustment. All remain `initial_model_awaiting_refinement`. Their silhouettes and patterns are stylized, and several still rely on related-species starting geometry. This is not evidence that they are 90% accurate.

## What changed in the renderer

The renderer can draw outlined diamonds, oval markings, dorsal zigzags, paired spots, paired neck stripes, asymmetric rattlesnake tail bands, an adjustable rattle, and a dark/yellow lateral body with a spotted paddle. Palette and geometry remain editable. The review-plate export preserves SVG aspect ratio instead of stretching drawings. A non-pit-viper preset will not render a heat pit from a stale landmark.

For non-cobras, dorsal and ventral controls change surface details on the **same projected outline**. They do not establish an independently modeled top, side, front or underside. Even separate cobra presentations are illustrations, not calibrated reconstructions. Missing angles, uncertain identity, individual variation, coarse markings, and taxonomy questions remain in the per-preset evidence flags.

Two useful reference checks: [NCBI taxonomy](https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id=101163) documents the shore-pit-viper synonym; the [Reptile Database](https://reptile-database.reptarium.cz/Hypnale/hypnale) diagnosis says *Hypnale hypnale* lacks a raised snout tip despite its common name. The [Australian Museum](https://australian.museum/learn/animals/reptiles/yellow-bellied-sea-snake/) describes the dark upper body, yellow lower half and spotted paddle of the yellow-bellied sea snake.

## Remaining work

The status ledger distinguishes untouched scaffold presets from reference-informed drafts. Both require more work. Obtain clean, identifiable, license-documented reference views for missing angles; fit species-specific heads, outlines, and patterns; and have a qualified reviewer check them against references. Set a measurable review protocol before reporting any percentage accuracy. Do not change image acceptance or training eligibility just because a photo informed an illustration.
