# Post-download notes: remaining species

Updated: 2026-11-20T09:23:04.180471+00:00

Attempted **140 of 140** remaining species labels. Downloaded **1073 candidate photo records** in these new batches (some can share identical image content).

## Scope and interpretation

One species per folder, continuing numbering after pilot 009. Each search examines at most 20 research-grade observation records and selects up to 10 CC0/CC BY photo candidates, preferring different observations and at most two photos per observation. Photos must have attribution and reported dimensions of at least 512 pixels in both directions. Requests are sequential and cached. Downloads are capped at 20 MB each.

These are filtered availability samples, not an exhaustive internet search. A skip does not prove no photos exist elsewhere. Photo licensing is checked independently of observation licensing. Provider species labels remain provisional. Downloaded images are NOT visually screened for injury, documents, occlusion, or identity; all new records are held out of rendering training until review under the image policy.

## Status counts

| Status | Species labels |
|---|---:|
| downloaded_partial | 37 |
| downloaded_target | 91 |
| skipped_no_licensed_observations | 11 |
| skipped_taxon_unresolved | 1 |

## Final verification

128 source labels have new downloads. The 1073 downloaded records contain 1063 distinct SHA-256 image contents and use 1,456,472,743 bytes on disk.

File checksums, image paths, actual minimum dimensions, per-observation limits, gallery generation, and rendering quarantine were checked. No new image has been approved for rendering training.

The source list includes Cryptelytrops purpureomaculatus and Trimeresurus purpureomaculatus, mapped to the same provider taxon. Their ten exact duplicate photo pairs are annotated; later copies have duplicate_of references and are excluded by the rendering exporter. Do not count these as independent species or specimens.

Original plus new batches cover 137 source labels representing 136 distinct provider taxon IDs. Provider IDs are not an expert taxonomic reconciliation.

The initial missing-dimensions handling failure for Bothrops asper was corrected and successfully retried. The previous attempt is preserved in progress.json and the collection log. No request/download failures remain.

Provider-reported dimensions differed from the downloaded original for 1 record(s); both reported and measured dimensions are retained in verification.json and the manifest.

Large-original preprocessing note: pilot_104_montivipera_raddei / inat_83527 is 13094 × 9199 pixels. Preserve the original and create a bounded-resolution derivative before future model ingestion. No resizing or training was performed.

## Skipped or failed species

| Species label | Status | Reason |
|---|---|---|
| Bothriechis thalassinus | skipped_no_licensed_observations | 0 observations matched the research-grade / licensed-photo query; no photo candidates passed all selection filters in the inspected sample. |
| Bothrops ayerbei | skipped_no_licensed_observations | 0 observations matched the research-grade / licensed-photo query; no photo candidates passed all selection filters in the inspected sample. |
| Bothrops barnetti | skipped_no_licensed_observations | 0 observations matched the research-grade / licensed-photo query; no photo candidates passed all selection filters in the inspected sample. |
| Bothrops colombiensis | skipped_taxon_unresolved | No unique supported species-name match. Provider candidates: Bothrops atrox |
| Bothrops pirajai | skipped_no_licensed_observations | 0 observations matched the research-grade / licensed-photo query; no photo candidates passed all selection filters in the inspected sample. |
| Bungarus sindanus | skipped_no_licensed_observations | 0 observations matched the research-grade / licensed-photo query; no photo candidates passed all selection filters in the inspected sample. |
| Naja katiensis | skipped_no_licensed_observations | 0 observations matched the research-grade / licensed-photo query; no photo candidates passed all selection filters in the inspected sample. |
| Naja nubiae | skipped_no_licensed_observations | 0 observations matched the research-grade / licensed-photo query; no photo candidates passed all selection filters in the inspected sample. |
| Ophryacus sphenophrys | skipped_no_licensed_observations | 0 observations matched the research-grade / licensed-photo query; no photo candidates passed all selection filters in the inspected sample. |
| Protobothrops kelomohy | skipped_no_licensed_observations | 0 observations matched the research-grade / licensed-photo query; no photo candidates passed all selection filters in the inspected sample. |
| Pseudechis papuanus | skipped_no_licensed_observations | 0 observations matched the research-grade / licensed-photo query; no photo candidates passed all selection filters in the inspected sample. |
| Toxicocalamus longissimus | skipped_no_licensed_observations | 0 observations matched the research-grade / licensed-photo query; no photo candidates passed all selection filters in the inspected sample. |

## All attempted species

| Species label | Folder | Downloaded | Observation groups | Status | Notes |
|---|---|---:|---:|---|---|
| Agkistrodon bilineatus | pilot_010_agkistrodon_bilineatus | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Agkistrodon contortrix | pilot_011_agkistrodon_contortrix | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Agkistrodon piscivorus | pilot_012_agkistrodon_piscivorus | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Agkistrodon taylori | pilot_013_agkistrodon_taylori | 6 | 3 | downloaded_partial | Only 6 of the target 10 candidates downloaded from this sample.  |
| Aspidelaps lubricus | pilot_014_aspidelaps_lubricus | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Aspidelaps scutatus | pilot_015_aspidelaps_scutatus | 10 | 8 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Atropoides picadoi | pilot_016_atropoides_picadoi | 4 | 2 | downloaded_partial | Only 4 of the target 10 candidates downloaded from this sample.  |
| Bitis caudalis | pilot_017_bitis_caudalis | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Bitis nasicornis | pilot_018_bitis_nasicornis | 10 | 7 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Bothriechis aurifer | pilot_019_bothriechis_aurifer | 5 | 4 | downloaded_partial | Only 5 of the target 10 candidates downloaded from this sample.  |
| Bothriechis bicolor | pilot_020_bothriechis_bicolor | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Bothriechis marchi | pilot_021_bothriechis_marchi | 3 | 2 | downloaded_partial | Only 3 of the target 10 candidates downloaded from this sample.  |
| Bothriechis nigroviridis | pilot_022_bothriechis_nigroviridis | 10 | 8 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Bothriechis schlegelii | pilot_023_bothriechis_schlegelii | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Bothriechis supraciliaris | pilot_024_bothriechis_supraciliaris | 7 | 5 | downloaded_partial | Only 7 of the target 10 candidates downloaded from this sample.  |
| Bothriechis thalassinus | pilot_025_bothriechis_thalassinus | 0 | 0 | skipped_no_licensed_observations | 0 observations matched the research-grade / licensed-photo query; no photo candidates passed all selection filters in the inspected sample. |
| Bothrocophias campbelli | pilot_026_bothrocophias_campbelli | 10 | 6 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Bothrops alternatus | pilot_027_bothrops_alternatus | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Bothrops asper | pilot_028_bothrops_asper | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Bothrops atrox | pilot_029_bothrops_atrox | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Bothrops ayerbei | pilot_030_bothrops_ayerbei | 0 | 0 | skipped_no_licensed_observations | 0 observations matched the research-grade / licensed-photo query; no photo candidates passed all selection filters in the inspected sample. |
| Bothrops barnetti | pilot_031_bothrops_barnetti | 0 | 0 | skipped_no_licensed_observations | 0 observations matched the research-grade / licensed-photo query; no photo candidates passed all selection filters in the inspected sample. |
| Bothrops caribbaeus | pilot_032_bothrops_caribbaeus | 2 | 1 | downloaded_partial | Only 2 of the target 10 candidates downloaded from this sample.  |
| Bothrops colombiensis | pilot_033_bothrops_colombiensis | 0 | 0 | skipped_taxon_unresolved | No unique supported species-name match. Provider candidates: Bothrops atrox |
| Bothrops cotiara | pilot_034_bothrops_cotiara | 1 | 1 | downloaded_partial | Only 1 of the target 10 candidates downloaded from this sample.  |
| Bothrops diporus | pilot_035_bothrops_diporus | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Bothrops erythromelas | pilot_036_bothrops_erythromelas | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Bothrops insularis | pilot_037_bothrops_insularis | 6 | 5 | downloaded_partial | Only 6 of the target 10 candidates downloaded from this sample.  |
| Bothrops jararacussu | pilot_038_bothrops_jararacussu | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Bothrops lanceolatus | pilot_039_bothrops_lanceolatus | 4 | 2 | downloaded_partial | Only 4 of the target 10 candidates downloaded from this sample.  |
| Bothrops leucurus | pilot_040_bothrops_leucurus | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Bothrops neuwiedi | pilot_041_bothrops_neuwiedi | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Bothrops pauloensis | pilot_042_bothrops_pauloensis | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Bothrops pictus | pilot_043_bothrops_pictus | 2 | 1 | downloaded_partial | Only 2 of the target 10 candidates downloaded from this sample.  |
| Bothrops pirajai | pilot_044_bothrops_pirajai | 0 | 0 | skipped_no_licensed_observations | 0 observations matched the research-grade / licensed-photo query; no photo candidates passed all selection filters in the inspected sample. |
| Bothrops punctatus | pilot_045_bothrops_punctatus | 7 | 4 | downloaded_partial | Only 7 of the target 10 candidates downloaded from this sample.  |
| Bungarus caeruleus | pilot_046_bungarus_caeruleus | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Bungarus candidus | pilot_047_bungarus_candidus | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Bungarus fasciatus | pilot_048_bungarus_fasciatus | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Bungarus flaviceps | pilot_049_bungarus_flaviceps | 10 | 7 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Bungarus multicinctus | pilot_050_bungarus_multicinctus | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Bungarus sindanus | pilot_051_bungarus_sindanus | 0 | 0 | skipped_no_licensed_observations | 0 observations matched the research-grade / licensed-photo query; no photo candidates passed all selection filters in the inspected sample. |
| Cerastes cerastes | pilot_052_cerastes_cerastes | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Cerastes vipera | pilot_053_cerastes_vipera | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Cerrophidion godmani | pilot_054_cerrophidion_godmani | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Cerrophidion sasai | pilot_055_cerrophidion_sasai | 9 | 6 | downloaded_partial | Only 9 of the target 10 candidates downloaded from this sample.  |
| Crotalus adamanteus | pilot_056_crotalus_adamanteus | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Crotalus basiliscus | pilot_057_crotalus_basiliscus | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Crotalus culminatus | pilot_058_crotalus_culminatus | 7 | 5 | downloaded_partial | Only 7 of the target 10 candidates downloaded from this sample.  |
| Crotalus durissus | pilot_059_crotalus_durissus | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Crotalus horridus | pilot_060_crotalus_horridus | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Crotalus oreganus | pilot_061_crotalus_oreganus | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Crotalus polystictus | pilot_062_crotalus_polystictus | 2 | 2 | downloaded_partial | Only 2 of the target 10 candidates downloaded from this sample.  |
| Crotalus scutulatus | pilot_063_crotalus_scutulatus | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Crotalus simus | pilot_064_crotalus_simus | 10 | 7 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Crotalus tigris | pilot_065_crotalus_tigris | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Crotalus tzabcan | pilot_066_crotalus_tzabcan | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Crotalus viridis | pilot_067_crotalus_viridis | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Cryptelytrops purpureomaculatus | pilot_068_cryptelytrops_purpureomaculatus | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Daboia russelii | pilot_069_daboia_russelii | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Daboia siamensis | pilot_070_daboia_siamensis | 10 | 9 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Deinagkistrodon acutus | pilot_071_deinagkistrodon_acutus | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Dendroaspis angusticeps | pilot_072_dendroaspis_angusticeps | 10 | 9 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Echis carinatus | pilot_073_echis_carinatus | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Echis ocellatus | pilot_074_echis_ocellatus | 1 | 1 | downloaded_partial | Only 1 of the target 10 candidates downloaded from this sample.  |
| Gloydius brevicaudus | pilot_075_gloydius_brevicaudus | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Hemachatus haemachatus | pilot_076_hemachatus_haemachatus | 10 | 9 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Hydrophis curtus | pilot_077_hydrophis_curtus | 10 | 6 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Hydrophis platurus | pilot_078_hydrophis_platurus | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Hydrophis schistosus | pilot_079_hydrophis_schistosus | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Hypnale hypnale | pilot_080_hypnale_hypnale | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Lachesis acrochorda | pilot_081_lachesis_acrochorda | 8 | 6 | downloaded_partial | Only 8 of the target 10 candidates downloaded from this sample.  |
| Lachesis melanocephala | pilot_082_lachesis_melanocephala | 2 | 1 | downloaded_partial | Only 2 of the target 10 candidates downloaded from this sample.  |
| Lachesis muta | pilot_083_lachesis_muta | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Lachesis stenophrys | pilot_084_lachesis_stenophrys | 1 | 1 | downloaded_partial | Only 1 of the target 10 candidates downloaded from this sample.  |
| Laticauda colubrina | pilot_085_laticauda_colubrina | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Macrovipera lebetina | pilot_086_macrovipera_lebetina | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Metlapilcoatlus nummifer | pilot_087_metlapilcoatlus_nummifer | 3 | 3 | downloaded_partial | Only 3 of the target 10 candidates downloaded from this sample.  |
| Micropechis ikaheka | pilot_088_micropechis_ikaheka | 2 | 1 | downloaded_partial | Only 2 of the target 10 candidates downloaded from this sample.  |
| Micrurus alleni | pilot_089_micrurus_alleni | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Micrurus altirostris | pilot_090_micrurus_altirostris | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Micrurus browni | pilot_091_micrurus_browni | 10 | 9 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Micrurus clarki | pilot_092_micrurus_clarki | 1 | 1 | downloaded_partial | Only 1 of the target 10 candidates downloaded from this sample.  |
| Micrurus corallinus | pilot_093_micrurus_corallinus | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Micrurus dumerilii | pilot_094_micrurus_dumerilii | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Micrurus frontalis | pilot_095_micrurus_frontalis | 5 | 3 | downloaded_partial | Only 5 of the target 10 candidates downloaded from this sample.  |
| Micrurus lemniscatus | pilot_096_micrurus_lemniscatus | 4 | 3 | downloaded_partial | Only 4 of the target 10 candidates downloaded from this sample.  |
| Micrurus mipartitus | pilot_097_micrurus_mipartitus | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Micrurus mosquitensis | pilot_098_micrurus_mosquitensis | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Micrurus nigrocinctus | pilot_099_micrurus_nigrocinctus | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Micrurus paraensis | pilot_100_micrurus_paraensis | 2 | 1 | downloaded_partial | Only 2 of the target 10 candidates downloaded from this sample.  |
| Micrurus spixii | pilot_101_micrurus_spixii | 5 | 3 | downloaded_partial | Only 5 of the target 10 candidates downloaded from this sample.  |
| Micrurus surinamensis | pilot_102_micrurus_surinamensis | 10 | 9 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Micrurus tschudii | pilot_103_micrurus_tschudii | 6 | 3 | downloaded_partial | Only 6 of the target 10 candidates downloaded from this sample.  |
| Montivipera raddei | pilot_104_montivipera_raddei | 3 | 3 | downloaded_partial | Only 3 of the target 10 candidates downloaded from this sample.  |
| Naja annulifera | pilot_105_naja_annulifera | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Naja atra | pilot_106_naja_atra | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Naja haje | pilot_107_naja_haje | 7 | 6 | downloaded_partial | Only 7 of the target 10 candidates downloaded from this sample.  |
| Naja kaouthia | pilot_108_naja_kaouthia | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Naja katiensis | pilot_109_naja_katiensis | 0 | 0 | skipped_no_licensed_observations | 0 observations matched the research-grade / licensed-photo query; no photo candidates passed all selection filters in the inspected sample. |
| Naja melanoleuca | pilot_110_naja_melanoleuca | 10 | 6 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Naja mossambica | pilot_111_naja_mossambica | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Naja nigricollis | pilot_112_naja_nigricollis | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Naja nubiae | pilot_113_naja_nubiae | 0 | 0 | skipped_no_licensed_observations | 0 observations matched the research-grade / licensed-photo query; no photo candidates passed all selection filters in the inspected sample. |
| Naja pallida | pilot_114_naja_pallida | 2 | 1 | downloaded_partial | Only 2 of the target 10 candidates downloaded from this sample.  |
| Naja sputatrix | pilot_115_naja_sputatrix | 10 | 7 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Notechis scutatus | pilot_116_notechis_scutatus | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Ophiophagus hannah | pilot_117_ophiophagus_hannah | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Ophryacus sphenophrys | pilot_118_ophryacus_sphenophrys | 0 | 0 | skipped_no_licensed_observations | 0 observations matched the research-grade / licensed-photo query; no photo candidates passed all selection filters in the inspected sample. |
| Ovophis convictus | pilot_119_ovophis_convictus | 5 | 3 | downloaded_partial | Only 5 of the target 10 candidates downloaded from this sample.  |
| Ovophis monticola | pilot_120_ovophis_monticola | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Ovophis okinavensis | pilot_121_ovophis_okinavensis | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Ovophis tonkinensis | pilot_122_ovophis_tonkinensis | 8 | 8 | downloaded_partial | Only 8 of the target 10 candidates downloaded from this sample.  |
| Porthidium lansbergii | pilot_123_porthidium_lansbergii | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Porthidium nasutum | pilot_124_porthidium_nasutum | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Porthidium ophryomegas | pilot_125_porthidium_ophryomegas | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Porthidium porrasi | pilot_126_porthidium_porrasi | 3 | 2 | downloaded_partial | Only 3 of the target 10 candidates downloaded from this sample.  |
| Protobothrops flavoviridis | pilot_127_protobothrops_flavoviridis | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Protobothrops kelomohy | pilot_128_protobothrops_kelomohy | 0 | 0 | skipped_no_licensed_observations | 0 observations matched the research-grade / licensed-photo query; no photo candidates passed all selection filters in the inspected sample. |
| Protobothrops mucrosquamatus | pilot_129_protobothrops_mucrosquamatus | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Pseudechis australis | pilot_130_pseudechis_australis | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Pseudechis papuanus | pilot_131_pseudechis_papuanus | 0 | 0 | skipped_no_licensed_observations | 0 observations matched the research-grade / licensed-photo query; no photo candidates passed all selection filters in the inspected sample. |
| Rhinobothryum bovallii | pilot_132_rhinobothryum_bovallii | 8 | 6 | downloaded_partial | Only 8 of the target 10 candidates downloaded from this sample.  |
| Sistrurus catenatus | pilot_133_sistrurus_catenatus | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Sistrurus miliarius | pilot_134_sistrurus_miliarius | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Toxicocalamus longissimus | pilot_135_toxicocalamus_longissimus | 0 | 0 | skipped_no_licensed_observations | 0 observations matched the research-grade / licensed-photo query; no photo candidates passed all selection filters in the inspected sample. |
| Trimeresurus albolabris | pilot_136_trimeresurus_albolabris | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Trimeresurus insularis | pilot_137_trimeresurus_insularis | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Trimeresurus puniceus | pilot_138_trimeresurus_puniceus | 9 | 6 | downloaded_partial | Only 9 of the target 10 candidates downloaded from this sample.  |
| Trimeresurus purpureomaculatus | pilot_139_trimeresurus_purpureomaculatus | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Trimeresurus stejnegeri | pilot_140_trimeresurus_stejnegeri | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Trimeresurus wiroti | pilot_141_trimeresurus_wiroti | 5 | 3 | downloaded_partial | Only 5 of the target 10 candidates downloaded from this sample.  |
| Tropidolaemus wagleri | pilot_142_tropidolaemus_wagleri | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Vipera aspis | pilot_143_vipera_aspis | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Vipera berus | pilot_144_vipera_berus | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Vipera kaznakovi | pilot_145_vipera_kaznakovi | 5 | 3 | downloaded_partial | Only 5 of the target 10 candidates downloaded from this sample.  |
| Vipera nikolskii | pilot_146_vipera_nikolskii | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Vipera orlovi | pilot_147_vipera_orlovi | 3 | 2 | downloaded_partial | Only 3 of the target 10 candidates downloaded from this sample.  |
| Vipera renardii | pilot_148_vipera_renardii | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
| Vipera ursinii | pilot_149_vipera_ursinii | 10 | 10 | downloaded_target | 10 candidates downloaded; visual and species review pending. |
