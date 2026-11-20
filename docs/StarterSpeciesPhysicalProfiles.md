# Starter species: physical reference profiles

Researched 2026-11-20. Scope: four species already present in the species catalog and pilot image collection. These are species reference descriptions, not annotations of individual pilot photos and not predictions from venom composition. No images were newly approved, no model was trained, and no venom-to-trait relationships are asserted.

## How to use these profiles

Separate anatomy, coloration, life stage, and pose. A raised neck or expanded hood is a display state; it does not change the underlying species. Treat colors and patterns as ranges of alternatives rather than combining every variation into one animal. Lengths below are total length unless explicitly labeled snout–vent length (SVL), which excludes the tail. Published typical sizes are descriptive summaries, not hard limits or sampling distributions.

Each species has sourced physical observations followed by proposed rendering controls. The controls are design recommendations, not measurements. Numerical head/body width ratios, tail fractions, exact color hex codes and distributions remain unmeasured; leave them unset until suitable measurements exist. Do not derive them from uncalibrated photographs.

## 1. Spectacled cobra — Naja naja

Catalog source label: `Naja naja`<br>
Pilot: `data/image_pilots/pilot_001_spectacled_cobra/`

### Physical characteristics

- **Size and stage:** Most adults are approximately 100–150 cm; occasional animals reach about 210–220 cm. Hatchlings are about 25–30 cm. These are literature summaries, not measurements of our photographed animals. [C1]
- **Body and head:** An elongated body with a rounded snout; the relaxed neck is not sharply separated from the head. Government guides variously describe the build as slender or stout, so a fixed thickness category is not justified. [C2, C3]
- **Surface:** Smooth, glossy body scales; a stout tail is described in the Rajasthan field guide. Detailed tail proportions remain unmeasured. [C3]
- **Dorsal appearance:** Ground colors include grey, yellowish, tan, brown, reddish and black. Some animals have speckling or indistinct bands. [C1]
- **Hood marking:** The familiar rear hood pattern consists of paired light eye-like marks with dark centers, connected by a curved light band. It may be weak or absent; absence alone does not exclude this species. [C1]
- **Underside:** Throat bands and ventral mottling vary. Some Sri Lankan animals have many ventral bands; northwestern melanistic adults may obscure the throat pattern. [C1]
- **Display:** Raising the forebody and spreading the hood is a defensive posture. Keep a relaxed-neck representation too. [C2]

### Variation and unresolved fields

Some northwestern populations darken with maturity. Geography and age therefore matter to appearance, but neither should be assigned from a single color. [C1] Sex-specific visible proportions and eye details are not populated in this first reference profile. Do not infer sex from these photos.

### Proposed 2D controls

- Separate `hood_expansion` from body width and `forebody_raise`.
- Store the hood mark on the **rear neck surface**, with presence and contrast independently adjustable. A front view should not show the rear mark through the body.
- Keep dorsal color, throat pattern and belly pattern in separate layers.
- Offer a brown, visibly marked reference preset and additional documented variants; label the preset as an illustration choice.
- Retain lateral and rear-hood views as complementary references. A ventral view can document throat variation but is not required for every rendering.

## 2. Coastal taipan — Oxyuranus scutellatus

Catalog source label: `Oxyuranus scutellatus`<br>
Pilot: `data/image_pilots/pilot_002_coastal_taipan/`

### Physical characteristics

- **Size:** Average total length is about 2 m; males grow slightly larger. Reports exceed 3 m, but the Australian Museum distinguishes these from measured specimens. Its cited large captive specimen measured 2.425 m SVL and 2.9 m total. [T1]
- **Body:** Robust, with a slender neck and a deep, rectangular head clearly distinct from it. This is not a uniformly thin-bodied template. [T1]
- **Head color:** The head is paler than the trunk, especially in young animals. It darkens with age while the snout remains pale in the museum's description. [T1]
- **Dorsal color:** Yellowish, reddish brown, dark brown or nearly black. Individuals can darken in winter and fade in summer. [T1]
- **Underside:** Cream to yellowish, with scattered orange blotches. [T1]
- **Eyes:** Large, with an orange-brown iris and round pupil. [T1]
- **Scales:** Mostly smooth, sometimes slightly keeled on the neck. The museum reports 21 or 23 midbody rows, 220–250 ventral scales, a single anal scale and divided subcaudals. These are anatomical reference counts, not pixel-scale texture settings. [T1]

### Variation and unresolved fields

The cited description supports age, season and sex variation; it does not supply enough measurements to assign distributions for head width, body thickness or tail length. Regional variation, including Papua New Guinea, needs further treatment before one preset is described as universal.

### Proposed 2D controls

- Model head depth, head width and neck width separately.
- Give the snout its own color region; do not lighten the entire body when adjusting it.
- Separate trunk color from the cream/yellow belly and orange spotting.
- Treat seasonal color and life stage as metadata-controlled alternatives, not venom effects.
- Use a lateral or oblique reference to establish head depth; an overhead image alone cannot establish it.
- Use neutral posture and a closed mouth for the first illustrative preset. This is a presentation choice.

## 3. Black mamba — Dendroaspis polylepis

Catalog source label: `Dendroaspis polylepis`<br>
Pilot: `data/image_pilots/pilot_003_black_mamba/`

### Physical characteristics

- **Size:** SANBI gives an average adult length of 2.0–2.5 m and a reported maximum of 4.3 m. The Eswatini Antivenom Foundation reports a local mature-adult average of 2.8 m. Preserve these as different source summaries rather than averaging them. [M1, M2]
- **Build and head:** Long and slender, with an elongated, often described as coffin-shaped head. “Coffin-shaped” is a qualitative description, not a polygon specification. [M1, M2]
- **Dorsal color:** Usually grey, olive or brown. Some older animals appear very dark; occasional mottling can form oblique flank markings. Juveniles are often light to medium grey. [M3]
- **Underside:** Light grey or white; posterior mottling can occur. [M2]
- **Mouth:** The interior is usually inky black, giving the species its common name. The African Snakebite Institute notes occasional light-mouthed individuals. [M3]
- **Display:** The forebody can rise, the mouth can gape, and the neck may form a narrow hood. [M1, M2]

### Variation and unresolved fields

Body shade and markings should remain variable. A black trunk is not the defining visual feature. Exact tail proportions, scale-row counts, eye geometry and sex-linked shape parameters remain unpopulated here rather than estimated from unrelated mamba species.

### Proposed 2D controls

- Start with a slender silhouette and an independently shaped elongated head.
- Keep mouth-interior color separate from external body color.
- Use low-contrast flank markings as an optional variant, not a compulsory pattern.
- Make neck flattening a display parameter distinct from the cobra's broad hood.
- A neutral, closed-mouth reference should still be recognizable through silhouette and coloration; do not require an open-mouth threat display for every output.
- Record full-body and head references separately because close head crops cannot establish body proportions.

## 4. Western diamondback rattlesnake — Crotalus atrox

Catalog source label: `Crotalus atrox`<br>
Pilot: `data/image_pilots/pilot_004_western_diamondback/`

### Physical characteristics

- **Size:** The Arizona–Sonora Desert Museum gives a usual range of 3–5 ft (approximately 0.9–1.5 m), with some reaching 7 ft (approximately 2.1 m). [R1]
- **Body and head:** Heavy-bodied, with a narrow neck and broad triangular head. Pupils are elliptical; dorsal scales are keeled. [R2]
- **Dorsal pattern:** Brown or black diamond-like blotches with pale borders on a variable grey, brown, olive, tan or yellowish ground. Pattern contrast can be muted. [R2]
- **Face:** Heat-sensing pits lie between the nostrils and eyes. [R1] A pale diagonal stripe behind the eye crosses the upper lip before the jaw ends; this is one useful comparison with the similar Mojave rattlesnake, not a standalone identification test. [R2]
- **Tail:** Broad black and white rings of roughly similar width precede the segmented rattle. The ring next to the rattle is usually black. [R2]
- **Age variation:** Young animals often have clearer markings. Newborns have a button rather than a developed rattle. [R2]
- **Rattle variation:** Segments accumulate with shedding and can break off; segment count is not a reliable age estimate. [R1]

### Variation and unresolved fields

Do not require exactly equal tail bands or identical diamonds. Belly coloration and sex-specific proportions are left unset in this first profile. Do not copy these from the eastern diamondback, a different species.

### Proposed 2D controls

- Keep head width, neck width and trunk thickness independent.
- Treat dorsal diamonds, facial stripe, tail rings and rattle as separate visual regions.
- Use a keeled surface treatment at close scale without making distant images unnaturally rough.
- Keep rattle segment count independent of inferred age. A button is normal for a neonate; a broken adult rattle is not the preferred healthy reference preset.
- Prefer a full-body lateral/oblique reference with the tail visible, plus a head close-up for the face. Missing tail visibility is a framing limitation, not proof that the rattle is absent.

## Shared representation for the future renderer

| Field group | What to store | Unknown handling |
|---|---|---|
| Identity | Catalog species ID, exact source label, pilot batch | Never merge species based only on appearance |
| Scale | Total length or SVL, units, life stage, source | Do not interchange total length and SVL |
| Shape | Trunk build, head outline, head–neck separation, tail form | Numerical ratios remain null until measured |
| Surface | Smooth/keeled texture and relevant scale regions | Keep counts separate from visual texture |
| Appearance | Dorsal, lateral, ventral, head and mouth regions | Unknown does not mean absent |
| Pattern | Pattern family, position, contrast and documented variants | Atypical does not automatically mean erroneous |
| Display | Neck expansion, raised forebody, mouth opening, body pose | Pose is separate from anatomy |
| Variation | Age, sex, locality, season and source-specific scope | Leave unsupported values unknown |
| Evidence | Source URL, claim scope, qualitative versus measured | Rendering choices are explicitly separate |

The first implementation can use four curated illustrative presets. Their proportions would be design settings until measured. Matching venom profiles to a species preset is not evidence that changing a toxin percentage causes a hood, diamond pattern, body color or head shape. That mapping remains a separate research/design task.

## Sources

- **C1:** Wüster, W. (1998), *The cobras of the genus Naja in India*, Hamadryad 23:15–32. Primary taxonomic study; use the Naja naja description, not the neighboring species descriptions. [Author-uploaded paper](https://www.academia.edu/1479078/W%C3%BCster_W_1998_The_cobras_of_the_genus_Naja_in_India_Hamadryad_23_15_32).
- **C2:** India's National Centre for Disease Control, medically important snakes guide, spectacled cobra entry. [Government guide](https://ncdc.mohfw.gov.in/uploads/pdf/Final_Medically%20imp%20snakes_English_231016_102536_260715_140946.pdf). Relevant text was available through indexed extraction; direct retrieval timed out.
- **C3:** Rajasthan Forest Department, *Amphibians & Reptiles of Mukandra Hills Tiger Reserve*, spectacled cobra entry, printed page 68. [Government field guide](https://forest.rajasthan.gov.in/content/dam/raj/forest/ForestDepartment/PDFs/Preliminary-Birds-guide-/Reptiles%20%26%20Amphibians%20book%20of%20MHTR0.pdf). Entry accessed through indexed extraction.
- **T1:** Australian Museum, [Coastal Taipan](https://australian.museum/learn/animals/reptiles/coastal-taipan/), identification section.
- **M1:** South African National Biodiversity Institute, [Black mamba](https://www.sanbi.org/animal-of-the-week/black-mamba/), recognition section. Used only for the cited external-description facts; its fang-mechanics wording is not adopted.
- **M2:** Eswatini Antivenom Foundation, [Black Mamba fact sheet](https://eswatiniantivenom.org/digital-fact-sheets/fact-sheet-black-mamba/), description and display only; no treatment guidance is reproduced.
- **M3:** African Snakebite Institute, [Black Mamba](https://www.africansnakebiteinstitute.com/snake/african-snakes-black-mamba/), external coloration and display.
- **R1:** Arizona–Sonora Desert Museum, [Western Diamondback Rattlesnake](https://desertmuseum.org/kids/facts/?animal=Western+Diamondback+Rattlesnake), size, pit organs and rattle notes.
- **R2:** CaliforniaHerps, [Western Diamond-backed Rattlesnake](https://www.californiaherps.com/snakes/pages/c.atrox.html), descriptive field account and documented photo comparisons. This is a specialist reference account, not a primary morphometric study; its numerical measurements were not used to fit any shape model.
