# ASE-DB Index

*From [[notes/DATASET]] (HuggingFace) and [[notes/OMOL_README]]*

## What It Is

The ASE-DB is the canonical index for the OMol25 dataset. It stores one entry per DFT calculation as an ASE `Atoms` object in LMDB format, readable via `fairchem`'s `AseDBDataset`. The **4M split** (`train_4M.tar.gz`, 19 GB) is the working set for our prototype.

```python
from fairchem.core.datasets import AseDBDataset

dataset = AseDBDataset({"src": "path/to/train_4M/"})
atoms = dataset.get_atoms(0)
```

## Split Sizes

| Split | Count | Size |
|---|---|---|
| Train (4M) | 3,986,754 | 19 GB |
| Train (All, OMol-0) | 101,666,280 | 456 GB |
| Train (Neutral, OMol-0) | 34,335,828 | 101 GB |
| Val | 2,762,021 | 20 GB |
| Test | 2,805,046 | 8 GB |
| Train (All, OMol-1) | 139,836,891 | 592 GB |

The 4M split is a **random sample** of the full OMol-0 training set.

## Per-Structure Data

Each entry is an ASE `Atoms` object with:
- `atoms.positions` — Cartesian coordinates (Å)
- `atoms.get_atomic_numbers()` — element array
- `atoms.get_potential_energy()` — DFT total energy (eV)
- `atoms.get_forces()` — per-atom forces (eV/Å)

## `atoms.info` Metadata Fields

| Field | Type | Notes |
|---|---|---|
| `source` | str | Full path including filename, e.g. `omol/electrolytes/.../step3/orca.tar.zst`. `os.path.dirname(source)` gives the Eagle directory path matching [[notes/directory-structure-analysis]] and `4m_paths.txt`. |
| `reference_source` | str/None | Internal identifier, often None |
| `data_id` | str | Domain label. Known: `elytes`. Other values TBD — see open question in [[notes/open_questions]]. |
| `charge` | int | Total molecular charge |
| `spin` | int | Spin **multiplicity** (2S+1). 1 = singlet, 3 = triplet, etc. NOT unpaired electron count. |
| `num_atoms` | int | Atom count |
| `num_electrons` | int | Total electron count |
| `num_ecp_electrons` | int | ECP electrons (nonzero for heavy elements using pseudopotentials) |
| `n_scf_steps` | int | Number of SCF iterations to convergence |
| `n_basis` | int | Number of basis functions (scales ~N³ with atom count) |
| `unrestricted` | bool | `True` for UKS (open-shell), `False` for RKS (closed-shell) |
| `nl_energy` | float | VV10 nonlocal dispersion energy (eV) |
| `integrated_densities` | array[3] | [α electrons, β electrons, total] — sanity check |
| `homo_energy` | array | HOMO energy (eV) |
| `homo_lumo_gap` | array | HOMO-LUMO gap (eV) |
| `s_squared` | float | ⟨S²⟩ — measures spin contamination |
| `s_squared_dev` | float | Deviation of ⟨S²⟩ from ideal value |
| `warnings` | list | ORCA warning messages from the calculation |
| `mulliken_charges` | array[N] | Per-atom Mulliken partial charges |
| `lowdin_charges` | array[N] | Per-atom Löwdin partial charges |
| `nbo_charges` | array[N] | Per-atom NBO partial charges (not always available) |
| `composition` | str | Hill-notation composition string, e.g. `B1Br1C27H36N2O16S1` |

**Unrestricted-only fields** (present when `unrestricted=True`):

| Field | Notes |
|---|---|
| `mulliken_spins` | Per-atom Mulliken spin populations |
| `lowdin_spins` | Per-atom Löwdin spin populations |
| `nbo_spins` | Per-atom NBO spin populations (when available) |

## Relationship to the Globus Collection

The `source` field ties the ASE-DB directly to the Eagle filesystem:

```python
import os
atoms = dataset.get_atoms(idx)
eagle_path = os.path.dirname(atoms.info["source"])
# e.g. "omol/electrolytes/solvated_090624/benzothiadizaole_mol1129_solv7_0_1/step3"
# This matches a path in 4m_paths.txt and a directory in the Globus collection.
```

## Relationship to Santiago's Descriptor Layer

Santiago's LMDB will use the same path keys. The join is:
- ASE-DB key → `atoms.info["source"]` → `os.path.dirname()` → Eagle path
- Santiago LMDB key → Eagle path directly

Fields that overlap (ASE-DB already has them, Santiago's `orca.json` also parses them):
- HOMO/LUMO energies, Mulliken/Löwdin charges

Fields Santiago adds that are NOT in the ASE-DB:
- Mayer charges and bond orders
- QTAIM critical point properties
- Multiple charge schemes (Hirshfeld, ADCH, CM5, Becke)
- Fuzzy bond orders
- ALIE surface descriptors, molecular volume

See [[notes/santiago-derived-descriptors]].

## Index Build Notes

For the parquet index (see [[2026-03-09-omol-filter-interface-design]]):

- `domain` ← `atoms.info["data_id"]` (no path parsing needed)
- `eagle_path` ← `os.path.dirname(atoms.info["source"])`
- `has_<element>` ← `atoms.get_atomic_numbers()` or parse `atoms.info["composition"]`
- `charge`, `spin`, `num_atoms`, `num_electrons`, `n_basis`, `homo_lumo_gap`, `unrestricted`, `s_squared` ← direct from `atoms.info` at zero extra cost
- `file_sizes` ← not in ASE-DB; requires separate Globus/S3 HeadObject pass

The 4M split (3,986,754 entries) iterates in minutes on a single machine.

See also: [[notes/ase-db-exploration|ase-db-exploration]]