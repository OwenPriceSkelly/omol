# Open Questions

## Active

### What is the file size distribution across the full 4M?
Six hand-sampled points show ~100× variation (0.8 MB to 94 MB per structure). Need a broader sample to estimate total dataset size and calibrate transfer size estimates in the manifest service. S3 `HeadObject` could be used for cheap per-file size queries.

### Is getting per-structure file sizes feasible for the prototype index?
The parquet index design calls for a `file_sizes` struct column, but file sizes are not in the ASE-DB — they require a separate pass. Options: (a) `globus ls -l` on all 4M paths (slow), (b) S3 `HeadObject` against `archive/hot/` and `archive/warm/` prefixes (fast/cheap, but requires confirming S3 credentials are still valid — they may be expired), (c) per-subdataset averages derived from the size samples in [[notes/directory-structure-analysis]] (good enough for order-of-magnitude estimates). Answer determines whether `file_sizes` is in the prototype or deferred. See [[docs/plans/2026-03-09-omol-filter-interface-design|2026-03-09-omol-filter-interface-design]]

### How complete is Santiago's descriptor layer, and when does it arrive at ALCF?
Santiago is generating Multiwfn-derived descriptors (QTAIM, bond orders, multiple charge schemes, ALIE surface properties, parsed orca.out) for the OMol25 structures. Not yet complete for all 4M. Plans to convert to LMDBs keyed by path. Storage space at ALCF is an open question. See [[notes/santiago-derived-descriptors]].

### What is the true extent of missing/corrupted files across all 4M paths?
`missing.txt` and `failures.txt` in `test/` represent a spot-check of ~20 paths, not a full audit. 6 of those failed. The `reverifier_progress.json` (a second pass) also exists — but we don't know its scope. The index build needs to handle missing files gracefully; the actual missing rate is unknown. See [[notes/s3-access-and-storage-tiers]]. (NOTE: these are likely just out of date - we can assume for now that files are not missing or corrupted)

### What is the `subsampling` tag taxonomy?
~~The design plan ([[2026-03-09-omol-filter-interface-design]]) calls for a `subsampling` field. The right granularity is unclear: top-level directory name, `omol/` sub-batch name, or a coarser `ml_*` vs hand-generated distinction?~~

---

## Resolved

### Are all three files present in every directory? (YES — with caveats)
Confirmed via `globus ls` across all depth levels and domains: every sampled directory contains `orca.tar.zst`, `orca.gbw.zstd0`, and `density_mat.npz`. However, a spot-check verification found 6–8 paths with missing files. The true missing rate across 4M is unknown. See [[notes/s3-access-and-storage-tiers]].

### Is there an alternative to Globus for accessing the data? (NO — S3 was ingestion-only)
S3 (`s3://opencatalysisdata`) was almost certainly Argonne's internal ingestion path for pulling the 4M subset from Meta's infrastructure onto Eagle — not a public access path. Access may already be expired. Globus is the only documented and supported access path for external researchers. See [[notes/s3-access-and-storage-tiers]].

### What is the `test/` subdirectory?
A staging area used for a spot-check verification of the upload. Contains sample paths from 9 subdatasets and associated verifier progress/failure files. See [[notes/s3-access-and-storage-tiers]].

### What does `omol25_downloader.py` tell us about the path structure?
Confirms all three files per directory; reveals S3 bucket name, hot/warm tier split, and that the paths file is available as `archive/hot/4m_paths.txt.gz` on S3. See [[notes/s3-access-and-storage-tiers]].

### Is the trailing `_N_N` pattern charge and spin multiplicity? (YES)
Confirmed by [[notes/DATASET]]: `spin: 1` for a closed-shell restricted calculation. Second number is multiplicity (2S+1), not UHF unpaired-electron count. See [[notes/directory-structure-analysis]].

### Do all directories contain the same files regardless of depth/domain? (YES)
Confirmed across depth-2 (flat community datasets), depth-4 (omol/metal_organics/restart5to6), depth-5, and depth-6. See [[notes/directory-structure-analysis]].

### Does the ASE-DB carry an explicit domain label? (YES — `data_id`)
`atoms.info["data_id"]` contains the domain string (e.g., `elytes`). No path parsing needed for domain assignment. See [[notes/DATASET]] and [[notes/ase-db]].

### Are OMol-1 and OPoly26 in scope for the filter interface prototype? (NO — but design for extensibility)
The prototype covers the OMol-0 4M split. OMol-1 (~140M structures) and OPoly26 (~6M polymers) use the same ASE-DB format and DFT settings; extending the index to cover them is mechanical. The index schema and build pipeline should be designed with this extension in mind even if execution is deferred.

### What are the `data_id` string values for all four domains? (RESOLVED — 10 values total)
Full scan of 3,986,754 entries via [[notes/ase-db-exploration]]. The four large domains: `biomolecules` (20.1%), `elytes` (20.1%), `metal_complexes` (20.0%), `reactivity` (19.8%). Community datasets: `ani2x`, `trans1x`, `geom_orca6`, `rgd`, `orbnet_denali`, `spice`. Note `reactivity` was not on the original shortlist — it covers `ani1xbb`, `pmechdb`, `rmechdb`, `tm_react`. Full top-level-dir → data_id mapping in [[notes/ase-db-exploration#1-data_id-values]].

### Are all optimization steps indexed in the ASE-DB, or only final geometries? (RESOLVED — individual steps ARE indexed)
1,064,738 entries (26.7%) have a `/stepN/` path component, across 970,214 unique parent paths. Most parents contribute only 1 step (91.3%), but a parent can contribute many scattered steps (e.g., steps [5, 28, 36, 40, 45, 46]). Steps are not stored as full sequential trajectories — each is an independent entry. See [[notes/ase-db-exploration#2. Optimization Steps]].

### What is the `subsampling` tag taxonomy? (RESOLVED — 33 tags, use top-level dir + omol/ sub-batch)
Confirmed strategy: top-level directory for non-`omol/` paths; `omol/<second-component>` for omol paths. Yields 33 tags. Largest: `ani1xbb` (18.5%), `omol/metal_organics` (13.5%), `omol/electrolytes` (12.5%), `omol/solvated_protein` (9.6%). Full table in [[notes/ase-db-exploration#3-subsampling-tag-candidates]].

### How available are `nbo_charges` across the dataset? (RESOLVED — 67.2% present)
Present in 2,680,512 of 3,986,754 entries (67.2%); absent in 32.8%. Per-domain breakdown not yet done. See [[notes/ase-db-exploration#4-nbo-charge-availability]].
