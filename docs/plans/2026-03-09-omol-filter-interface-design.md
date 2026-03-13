# OMol25 Filter Interface — Design Document

*Date: 2026-03-09 — Updated 2026-03-13*

## Problem

The OMol25 dataset contains ~100M DFT calculations stored on Argonne's Eagle filesystem, accessible via Globus. There is currently no way for an external researcher to answer "how much data matches my criteria, and how do I get it?" without downloading the full ASE-DB index and writing custom filtering code.

The goal is a lightweight interface that lets exploratory users filter by chemical properties, get an instant order-of-magnitude estimate of how much data they're selecting, and produce a Globus transfer manifest for the subset they want.

## Design Principles

- **4M-first, scale-ready**: prototype against the 4M ASE-DB split; no architectural changes needed to scale to the full dataset. (The full OMol25 corpus is now ~140M structures across OMol-0 and OMol-1, with OPoly26 adding ~6M more — "100M" is no longer the right ceiling.)
- **No pre-computation required**: the system works correctly from a cold start using columnar scans. Pre-aggregated statistics can be slotted in later as a performance optimization without changing any interfaces.
- **Manifest-first transfer**: the prototype produces a file manifest the user hands to Globus. First-class Globus Auth integration (service-initiated transfers) is a clear v2 story.
- **Extensible filter spec**: the query data structure is typed and versioned, not a DSL string. New filter dimensions are additive.

---

## Layer 1: The Index

A single parquet file (or partitioned set at 100M scale) with one row per structure.

### Columns

**Element presence** (~90 columns, generated from the periodic table):
- `has_H`, `has_C`, `has_Fe`, ... — boolean

These are the primary query columns for the prototype. They compress extremely well in parquet's columnar encoding and map directly to fast AND/NOT operations.

**Scalar properties** (available at no extra cost from `atoms.info` during the ASE-DB scan):
- `charge` — int
- `spin` — int (multiplicity, 2S+1)
- `num_atoms` — int
- `num_electrons` — int
- `unrestricted` — boolean
- `homo_lumo_gap` — float (eV)
- `n_basis` — int

These are cheap to include — the index build already iterates every structure, and `atoms.info` carries all of these. No second pass required. Energy and forces are omitted (stored separately as tensors, not scalars).

**Provenance / routing**:
- `domain` — categorical, sourced from `atoms.info["data_id"]` (e.g. `elytes`). See open question 3 for full `data_id` taxonomy.
- `subsampling` — top-level directory name (34 distinct values; see [[directory-structure-analysis]] for taxonomy). Encodes subdataset origin at the right granularity for routing and display.
- `eagle_path` — `os.path.dirname(atoms.info["source"])`, matching Globus collection paths exactly
- `file_sizes` — struct with sizes (bytes) for each file type: `orca_tar_zst`, `gbw`, `density_mat_npz`. **Not available from the ASE-DB** — requires a separate pass. See open question 4.

### Extensibility

The filter spec is additive. New filter types (e.g. range filters on `num_atoms`, `charge`, `homo_lumo_gap`) require adding a field to the spec and a clause to the DuckDB executor — no other changes. OMol-1 and OPoly26 are out of scope for the prototype but use the same ASE-DB format; extending the index to cover them is mechanical (point the build script at the additional datasets).

### Build Pipeline

A one-time extraction script over the ASE-DB:

```python
from fairchem.core.datasets import AseDBDataset
import os

dataset = AseDBDataset({"src": "path/to/train_4M/"})
for idx in range(len(dataset)):
    atoms = dataset.get_atoms(idx)
    # elements → has_<element> booleans (from atoms.get_atomic_numbers() or atoms.info["composition"])
    # domain ← atoms.info["data_id"]  (e.g. "elytes" — NOT parsed from source path)
    # subsampling ← top-level directory: atoms.info["source"].split("/")[0]
    # eagle_path ← os.path.dirname(atoms.info["source"])
    # scalar columns ← atoms.info["charge"], ["spin"], ["num_atoms"], ["num_electrons"],
    #                   ["unrestricted"], ["homo_lumo_gap"], ["n_basis"]
    # file_sizes ← NOT available here; requires separate pass (see open question 4)
```

Output is written to `omol_index.parquet`. At 4M rows this runs in minutes on a machine with the ASE-DB locally available. Same script at larger scale, longer runtime.

---

## Layer 2: The Query Abstraction

### Filter Spec

A plain JSON-serializable structure that describes what the user wants, without encoding how to execute it:

```json
{
  "must_have": ["Fe", "N"],
  "must_not_have": ["La", "Ce", "Pr"],
  "domain": "metal_complex",
  "num_atoms": {"min": 10, "max": 100},
  "charge": 0
}
```

This spec is the contract between all clients and the backend. It is the abstraction boundary where pre-aggregation routing will be added later: "does this spec match a pre-computed histogram bucket? serve that. otherwise, fall back to DuckDB scan."

New filter types (e.g. `{"transition_metal_count": {"min": 3}}`) are additive — existing specs continue to work, and unsupported fields return a clear error rather than silent failure.

### Execution

The default executor translates the filter spec to a DuckDB query against the parquet index. A query produces one of two result types:

- **Count result**: `{count: N, estimated_gb: X}` — computed from row count and summed `file_sizes`
- **Manifest result**: list of `(eagle_path, file_sizes)` tuples for all matching rows

The executor is the only component that knows about DuckDB or parquet. Everything above it speaks filter specs and result types.

---

## Layer 3: The Service

A stateless REST API. No database, no session state. Holds the parquet index in memory at 4M scale; queries from disk at 100M.

### Endpoints

**`POST /query/count`**

Accepts a filter spec. Returns count and estimated transfer size. This is the "pre-query query" — fast enough for interactive use, called on every filter change in the UI.

```json
// response
{"count": 14200, "estimated_gb": 56.3}
```

**`POST /query/manifest`**

Accepts a filter spec, an optional `format` parameter, and an optional `file_types` parameter. Returns a manifest the user can pass directly to the Globus CLI to initiate a transfer.

**`file_types`** — controls which files are included per structure. Default is all three. `file_types=["orca_tar_zst"]` produces a hot-tier-only manifest (ORCA text outputs only — energies, forces, NBO charges), substantially smaller than a full transfer. This maps directly onto the underlying hot/warm storage tier split: `orca.tar.zst` is hot, `density_mat.npz` and `orca.gbw.zstd0` are warm. Users who only need to parse ORCA output text don't need wavefunction files.

**`format=globus_batch`** (default) — returns a plain-text file ready to pipe into `globus transfer --batch`:

```
# OMol25 subset — 14,200 systems
# Usage: globus transfer $EAGLE_EP:/ $DEST_EP:/local/path/ --batch manifest.txt
system_001/orca.tar.zst system_001/orca.tar.zst
system_002/orca.tar.zst system_002/orca.tar.zst
...
```

For full-directory transfers (`file_types` = all), lines use `--recursive`. For `file_types` subsets, lines enumerate individual files. Paths are relative to the Eagle collection root. All lines are submitted as a single Globus transfer task.

The batch file format is parsed by `globus transfer` using Python's `shlex` module — paths with spaces must be quoted, `#` lines are comments, blank lines are ignored.

**`format=json`** — returns structured JSON for programmatic use:

```json
{"manifest": [
  {"path": "system_001/", "files": {"orca_tar_zst": 1200000, "gbw": 540000, "density_mat_npz": 82000}},
  ...
]}
```

First-class Globus Auth (service holds a token, initiates transfer on the user's behalf) is deferred to v2 but is a natural extension of this endpoint.

---

## Layer 4: Clients

All three clients share one invariant: they construct filter specs and call the two API endpoints. Nothing else.

### Python Library

Core primitive. A `FilterSpec` dataclass that validates inputs and serializes to JSON. Two functions:

```python
count(spec: FilterSpec) -> CountResult
manifest(spec: FilterSpec, output_path: str) -> None
```

This is what the CLI and notebooks use directly.

### CLI

Thin wrapper over the library:

```
omol count --has Fe N --domain metal_complex
# → 14,200 structures (~56 GB)

omol manifest --has Fe N --domain metal_complex --output my_manifest.txt
# → wrote 14,200 paths to my_manifest.txt
# then: globus transfer $EAGLE_EP:/ $DEST_EP:~/data/ --batch my_manifest.txt
```

Argument parsing maps directly to `FilterSpec` fields. Adding a new filter type to the library automatically extends the CLI.

### Web Frontend

A static page hitting the REST API directly from the browser:
- Checkbox grid for elements (grouped by periodic table region)
- Dropdown for domain
- Sliders / range inputs for scalar filters (num_atoms, charge)
- Live count + size estimate, updated on every filter change (debounced, calls `/query/count`)
- File type selector (all / ORCA outputs only / wavefunction files only)
- "Generate manifest" button (calls `/query/manifest`, triggers download)

No server-side rendering required. Can be hosted as a static site alongside the API.

---

## Technology Stack

### Prototype: Parquet + DuckDB

The parquet file *is* the database — no server process to provision. DuckDB reads parquet natively, including over HTTP via byte-range requests, so the index can live on Eagle or any HTTP server without the API server downloading it first. Parquet's columnar encoding is particularly well-suited to our schema: ~90 low-cardinality boolean columns compress to almost nothing, and DuckDB only reads columns touched by a query.

The executor is the only component that knows about DuckDB or parquet. Everything above it speaks filter specs and result types, which makes the backend swappable.

### Upgrade Path: PostgreSQL

If query concurrency becomes a bottleneck (DuckDB is in-process; it doesn't parallelize across simultaneous API requests without multiple workers), the natural upgrade is PostgreSQL with GIN indexes on the element columns. The migration path is mechanical:

1. Load the parquet index into a Postgres table (one-time, `COPY FROM` or via pandas)
2. Add a GIN index per element column — these map directly to the AND/NOT boolean query pattern
3. Swap the DuckDB executor for a Postgres executor behind the same interface

No changes to the filter spec, API endpoints, or clients. ClickHouse is also worth considering at very high scale (100M rows + high concurrency), with the same swap-in path.

Parquet remains the canonical source of truth regardless of backend — it's portable, versionable, and readable by the broader scientific Python ecosystem.

---

## What Is Explicitly Out of Scope (Prototype)

- Pre-aggregated statistics — slot in behind the query abstraction later
- Globus Auth / service-initiated transfers — v2
- User accounts, saved queries, transfer history
- The "data enclave" / remote compute model discussed in the meeting — longer-term
- OMol-1 and OPoly26 datasets — same ASE-DB format and DFT settings as OMol-0, so extension is mechanical (point the build script at additional datasets, union the parquet files). Extensibility to cover these should be a priority when designing the index schema and build pipeline, even if execution is deferred.

---

## Open Questions

1. **Index hosting**: Where does `omol_index.parquet` live? On Eagle (served via the API), or mirrored somewhere with lower latency (e.g. a small VM)?
2. **API hosting**: Who runs the API server, and where? Argonne, UChicago, or a lightweight cloud VM?
3. ~~**Manifest format**~~: Resolved. `globus transfer --batch` expects a plain-text file with one `SOURCE_PATH DEST_PATH` pair per line (parsed via Python `shlex`). Per-line `--recursive` flag for directories. Source/dest prefixes on the command line allow relative paths in the batch file. The manifest endpoint defaults to this format.
4. **`data_id` values for all domains**: We know `elytes`. The other domain values (biomolecules, metal complexes, small molecules/community data) need to be confirmed from the ASE-DB before the `domain` filter can be mapped correctly. See [[open_questions]].
5. **`file_sizes` column feasibility**: Getting per-structure file sizes requires a separate pass beyond the ASE-DB scan — either `globus ls -l` (slow at 4M scale) or S3 `HeadObject` against `archive/hot/` and `archive/warm/` prefixes (fast, cheap, but requires confirming S3 credentials are still valid). Is this feasible for the prototype? If not, fallback is per-subdataset averages derived from the size samples in [[directory-structure-analysis]]; these would be good enough for order-of-magnitude transfer estimates.
