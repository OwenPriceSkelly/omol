# TODO

## Needs ASE-DB access (fairchem + train_4M)

- [x] Confirm `data_id` values for all four domains — sample one entry per top-level directory group and record the strings. Resolves [[notes/open_questions#what-are-the-data_id-string-values-for-all-four-domains]] — see [[notes/ase-db-exploration]]
- [x] Determine whether all optimization steps are indexed or only final geometries — check a few `omol/` paths that have `/step0` through `/stepN` siblings and see if each step appears as a separate ASE-DB entry— see [[notes/ase-db-exploration]] 
- [x] Nail down the `subsampling` tag taxonomy — scan `atoms.info["source"]` path prefixes across the 4M and decide on the right granularity for the `subsampling` column in the parquet index -- see [[notes/ase-db-exploration]]
- [x] Check whether `nbo_charges` (and `nbo_spins`) are present for most structures or only a small subset — NBO is expensive and may have been skipped for large systems or certain domains. — see [[notes/ase-db-exploration]]

## Infrastructure

- [x] Get fairchem installed locally or on a compute node with access to train_4M
- [ ] Confirm storage allocation for Santiago's descriptor data at ALCF (follow up with Ben) NOTE: currently waiting to hear back from ALCF on proposal for more storage 

## Index build

- [ ] Decide on file size strategy for the prototype: per-subdataset averages from current samples vs. full per-structure pass. See [[notes/open_questions#Is getting per-structure file sizes feasible for the prototype index?]]
- [ ] Write the index extraction script (`scripts/build_index.py`) once ASE-DB questions above are resolved
