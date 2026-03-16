# TODO

## Needs ASE-DB access (fairchem + train_4M)

- [x] Confirm `data_id` values for all four domains — sample one entry per top-level directory group and record the strings. Resolves [[notes/open_questions#what-are-the-data_id-string-values-for-all-four-domains]] — see [[notes/ase-db-exploration]]
- [x] Determine whether all optimization steps are indexed or only final geometries — check a few `omol/` paths that have `/step0` through `/stepN` siblings and see if each step appears as a separate ASE-DB entry— see [[notes/ase-db-exploration]] 
- [x] Nail down the `subsampling` tag taxonomy — scan `atoms.info["source"]` path prefixes across the 4M and decide on the right granularity for the `subsampling` column in the parquet index -- see [[notes/ase-db-exploration]]
- [x] Check whether `nbo_charges` (and `nbo_spins`) are present for most structures or only a small subset — NBO is expensive and may have been skipped for large systems or certain domains. — see [[notes/ase-db-exploration]]

## Infrastructure

- [x] Get fairchem installed locally or on a compute node with access to train_4M
- [x] Confirm storage allocation for Santiago's descriptor data at ALCF (follow up with Ben) 
	- [ ] NOTE: currently waiting to hear back from ALCF on proposal for more storage. Exploration / infra for 4m not blocked on this. 
- [ ] Deploy FE to github pages or similar 
- [ ] CI / CD for deployments (modal app backend)
- [ ] Basic test suite 
- [ ] Publishing for CLI package 

## Spyhop — Index Build

- [x] Decide on file size strategy: n_basis regression from ~200 sampled structures. See [[docs/plans/2026-03-09-omol-filter-interface-design#File Size Strategy|design doc]]
- [x] Write the index extraction script (`spyhop/scripts/build_index.py`)
- [x] Run `build_index.py` against the 4M ASE-DB on Eagle to produce `omol_index.parquet`
- [x] Collect file size calibration sample via Globus SDK (`spyhop/scripts/estimate_file_sizes.py collect`)
- [x] Fit n_basis → file size regression models and backfill `file_sizes` column (`spyhop/scripts/estimate_file_sizes.py backfill`)
- [x] Run `backfill` to apply regression to full 4M index — run with `-o spyhop/index.parquet` (in-place, safe since pyarrow reads fully into memory before writing)
- [ ] (future) Replace estimated file sizes with true sizes — requires a full pass over the Eagle filesystem or Globus `ls -l` at scale; not needed for prototype
- [x] Upload index parquet to Modal Volume — in `spyhop-index` volume on garden-ai dev environment

## Spyhop — API & Clients

- [x] Implement FilterSpec dataclass and DuckDB query executor (`src/spyhop/query.py`)
- [x] Stand up FastAPI server as Modal app (`spyhop/app.py`) with `/query/count` and `/query/manifest` endpoints
- [x] Python client library wrapping the two endpoints (`src/spyhop/client.py`)
- [x] CLI (`spyhop count`, `spyhop manifest`) wrapping the library
- [x] Web frontend (`spyhop/index.html` — periodic table picker, live count, manifest download)
- [ ] Deploy via `modal deploy spyhop/app.py`
