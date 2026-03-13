# TODO

## Needs ASE-DB access (fairchem + train_4M)

- [ ] Confirm `data_id` values for all four domains — sample one entry per top-level directory group and record the strings. Resolves [[omol-notes/open_questions#what-are-the-data_id-string-values-for-all-four-domains]]
- [ ] Determine whether all optimization steps are indexed or only final geometries — check a few `omol/` paths that have `/step0` through `/stepN` siblings and see if each step appears as a separate ASE-DB entry. Resolves [[omol-notes/open_questions#are-all-optimization-steps-indexed-in-the-ase-db-or-only-final-geometries]]
- [ ] Nail down the `subsampling` tag taxonomy — scan `atoms.info["source"]` path prefixes across the 4M and decide on the right granularity for the `subsampling` column in the parquet index. Resolves [[omol-notes/open_questions#what-is-the-subsampling-tag-taxonomy]]
- [ ] Check whether `nbo_charges` (and `nbo_spins`) are present for most structures or only a small subset — NBO is expensive and may have been skipped for large systems or certain domains.

## Infrastructure

- [ ] Get fairchem installed locally or on a compute node with access to train_4M
- [ ] Confirm storage allocation for Santiago's descriptor data at ALCF (follow up with Ben)

## Index build

- [ ] Decide on file size strategy for the prototype: per-subdataset averages from current samples vs. full per-structure pass. See [[omol-notes/open_questions#is-getting-per-structure-file-sizes-feasible-for-the-prototype-index]]
- [ ] Write the index extraction script (`scripts/build_index.py`) once ASE-DB questions above are resolved
