# S3 Access and Storage Tiers

*2026-03-13, derived from `omol25_downloader.py` in `test/` at the Globus collection root*

## S3 Was the Ingestion Source, Not a Parallel Access Path

The downloader script (`omol25_downloader.py`) pulls from AWS S3 using boto3. This was almost certainly **Argonne's internal ingestion tool** — used to pull the 4M subset from Meta's infrastructure onto Eagle — not a public access path for researchers.

Evidence for this interpretation:
- The script lives in `test/` alongside the verifier, not in any public-facing location
- The S3 bucket (`opencatalysisdata`) is Meta/FAIR's own infrastructure, not an Argonne bucket
- Neither the OMOL_README nor DATASET.md mentions S3 at all — Globus is the only documented access path
- The bucket grants `s3:GetObject` but not `s3:ListBucket`, consistent with a scoped credential rather than a fully public dataset
- The internal `archive/hot/` and `archive/warm/` prefix structure looks like Meta's storage tiering, not a public release layout

**S3 access may no longer work** — the credential or public key that allowed Argonne's ingestion may have expired or been revoked. Globus is the access path for external researchers.

- **Bucket**: `opencatalysisdata` (Meta/FAIR internal)
- **Region**: not specified in the script

## Two Storage Tiers

Files within each calculation directory are split across two S3 prefixes:

| Tier | S3 prefix | Files |
|---|---|---|
| **Hot** | `archive/hot/<calc_path>/` | `orca.tar.zst` |
| **Warm** | `archive/warm/<calc_path>/` | `density_mat.npz`, `orca.gbw.zstd0` |

So the full S3 key for a file is, e.g.:
- `archive/hot/ani1xbb/aniBB_022_163758_0_1/orca.tar.zst`
- `archive/warm/ani1xbb/aniBB_022_163758_0_1/density_mat.npz`
- `archive/warm/ani1xbb/aniBB_022_163758_0_1/orca.gbw.zstd0`

**Implication**: the hot/warm split maps onto access patterns. `orca.tar.zst` (text output — NBO charges, property file, etc.) is expected to be accessed more frequently than the density matrix and GBW files. This is consistent with most users wanting to parse ORCA output text without needing raw wavefunctions.

## Paths File on S3

The 4M paths list is available as a gzip-compressed file:
- `archive/hot/4m_paths.txt.gz`

This is how new downloaders are expected to discover what paths exist, rather than listing the bucket.

## The `test/` Directory

The `test/` subdirectory in the Globus collection was used to run a **spot-check verification** of the upload. The `verifier_progress.json` shows 14 paths verified successfully and 6 failed — this was a sample of ~20 paths across the major subdatasets, not a full audit of all 4M. The subdirectories present under `test/` (ani1xbb, ani2x, geom_orca6, omol, orbnet_denali, pdb_fragments_300K, rpmd, spice, trans1x) reflect the sampled domains.

## Missing and Failed Files

`missing.txt` (8 paths) and `failures.txt` (6 paths) represent the output of the verification run:

**missing.txt** (paths where files were absent or inaccessible):
```
omol/metal_organics/restart5to6/job_1741594692_7193f6bc524b
ani1xbb/aniBB_008_369479_0_1
omol/electrolytes/solvated_090624/sulfite_ester_mol1207_solv9_0_1/step2
omol/solvated_protein/outputs_241002/spf_959718_0_2/step1
trans1x/t1x_rxn2310_1442_1089_0_1
pdb_fragments_300K/4idv_DBS01_state0_0_1_100056230_ligstate0_2_1
ani1xbb/aniBB_015_774115_1_3
rpmd/31_C2Cl2H4_3_group_5_shell_117_0_1
```

**failures.txt** (6 of the above that actively failed verification — subset of missing):
```
omol/metal_organics/restart5to6/job_1741594692_7193f6bc524b/
omol/electrolytes/solvated_090624/sulfite_ester_mol1207_solv9_0_1/step2/
trans1x/t1x_rxn2310_1442_1089_0_1/
pdb_fragments_300K/4idv_DBS01_state0_0_1_100056230_ligstate0_2_1/
ani1xbb/aniBB_015_774115_1_3/
rpmd/31_C2Cl2H4_3_group_5_shell_117_0_1/
```

**Critical caveat**: This was a spot-check of ~20 paths, not a full verification of all 3.99M. The true count of missing/corrupted files across the full dataset is unknown. The 6/14 failure rate in the spot-check (~43%) would be catastrophic if representative, but is almost certainly not — these were likely the known-bad paths that prompted the reverification run. The `reverifier_progress.json` (distinct from `verifier_progress.json`) suggests a second pass was done.

## Implications for the Index Build

- The index build script should be robust to missing files for individual paths — not every path in `4m_paths.txt` is guaranteed to have all three files present.
- File sizes for transfer estimation could be obtained by querying S3 `HeadObject` without downloading — this is cheap and works without `ListBucket` permission.
- The hot/warm tier distinction matters for the manifest service: if users only want `orca.tar.zst` (e.g., to parse NBO charges), they should be able to request hot-only transfers, which would be substantially faster and cheaper.
