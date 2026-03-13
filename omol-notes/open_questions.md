# Open Questions

## Active

### What are the `data_id` string values for all four domains?
We know `elytes` from [[DATASET]]. Need the values for biomolecules, metal complexes, and small molecules/community data. These become the `domain` column in the parquet index.

### What is the true extent of missing/corrupted files across all 4M paths?
`missing.txt` and `failures.txt` in `test/` represent a spot-check of ~20 paths, not a full audit. 6 of those failed. The `reverifier_progress.json` (a second pass) also exists — but we don't know its scope. The index build needs to handle missing files gracefully; the actual missing rate is unknown. See [[s3-access-and-storage-tiers]]. (NOTE: these are likely just out of date - we can assume for now that files are not missing or corrupted)

### What is the file size distribution across the full 4M?
Six hand-sampled points show ~100× variation (0.8 MB to 94 MB per structure). Need a broader sample to estimate total dataset size and calibrate transfer size estimates in the manifest service. S3 `HeadObject` could be used for cheap per-file size queries.

### Is getting per-structure file sizes feasible for the prototype index?
The parquet index design calls for a `file_sizes` struct column, but file sizes are not in the ASE-DB — they require a separate pass. Options: (a) `globus ls -l` on all 4M paths (slow), (b) S3 `HeadObject` against `archive/hot/` and `archive/warm/` prefixes (fast/cheap, but requires confirming S3 credentials are still valid — they may be expired), (c) per-subdataset averages derived from the size samples in [[directory-structure-analysis]] (good enough for order-of-magnitude estimates). Answer determines whether `file_sizes` is in the prototype or deferred. See [[docs/plans/2026-03-09-omol-filter-interface-design]].

### Are all optimization steps indexed in the ASE-DB, or only final geometries?
Many `omol/` paths have `/stepN` suffixes (steps 0–5+). It's unclear whether each step is a separate ASE-DB entry or if only converged structures are included.

### How complete is Santiago's descriptor layer, and when does it arrive at ALCF?
Santiago is generating Multiwfn-derived descriptors (QTAIM, bond orders, multiple charge schemes, ALIE surface properties, parsed orca.out) for the OMol25 structures. Not yet complete for all 4M. Plans to convert to LMDBs keyed by path. Storage space at ALCF is an open question. See [[santiago-derived-descriptors]].

### What is the `subsampling` tag taxonomy?
The design plan ([[2026-03-09-omol-filter-interface-design]]) calls for a `subsampling` field. The right granularity is unclear: top-level directory name, `omol/` sub-batch name, or a coarser `ml_*` vs hand-generated distinction?

---

## Resolved

### Are all three files present in every directory? (YES — with caveats)
Confirmed via `globus ls` across all depth levels and domains: every sampled directory contains `orca.tar.zst`, `orca.gbw.zstd0`, and `density_mat.npz`. However, a spot-check verification found 6–8 paths with missing files. The true missing rate across 4M is unknown. See [[s3-access-and-storage-tiers]].

### Is there an alternative to Globus for accessing the data? (NO — S3 was ingestion-only)
S3 (`s3://opencatalysisdata`) was almost certainly Argonne's internal ingestion path for pulling the 4M subset from Meta's infrastructure onto Eagle — not a public access path. Access may already be expired. Globus is the only documented and supported access path for external researchers. See [[s3-access-and-storage-tiers]].

### What is the `test/` subdirectory?
A staging area used for a spot-check verification of the upload. Contains sample paths from 9 subdatasets and associated verifier progress/failure files. See [[s3-access-and-storage-tiers]].

### What does `omol25_downloader.py` tell us about the path structure?
Confirms all three files per directory; reveals S3 bucket name, hot/warm tier split, and that the paths file is available as `archive/hot/4m_paths.txt.gz` on S3. See [[s3-access-and-storage-tiers]].

### Is the trailing `_N_N` pattern charge and spin multiplicity? (YES)
Confirmed by [[DATASET]]: `spin: 1` for a closed-shell restricted calculation. Second number is multiplicity (2S+1), not UHF unpaired-electron count. See [[directory-structure-analysis]].

### Do all directories contain the same files regardless of depth/domain? (YES)
Confirmed across depth-2 (flat community datasets), depth-4 (omol/metal_organics/restart5to6), depth-5, and depth-6. See [[directory-structure-analysis]].

### Does the ASE-DB carry an explicit domain label? (YES — `data_id`)
`atoms.info["data_id"]` contains the domain string (e.g., `elytes`). No path parsing needed for domain assignment. See [[DATASET]] and [[ase-db]].

### Are OMol-1 and OPoly26 in scope for the filter interface prototype? (NO — but design for extensibility)
The prototype covers the OMol-0 4M split. OMol-1 (~140M structures) and OPoly26 (~6M polymers) use the same ASE-DB format and DFT settings; extending the index to cover them is mechanical. The index schema and build pipeline should be designed with this extension in mind even if execution is deferred.
