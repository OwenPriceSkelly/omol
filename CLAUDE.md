# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains miscellaneous infrastructure and analysis work for the OMol25 dataset, maintained at Argonne National Laboratory. The big-picture goal is to build tooling that makes the dataset usable for science. This repository in particular is for exploring and understanding the dataset and for quick prototyping. 

An explicit early goal is to build up a personal knowledge base of context for ourselves in the omol-notes subdirectory. In particular, we maintain a [[open_questions]] living note for bookkeeping which can and should be updated frequently as the knowledge base grows. The user will want to interact with the notes as an obsidian vault, so links formatted like [[OMOL_README]] (or e.g. [[OMOL_README#Data Description]] for specific headings) are *extremely* valuable for cross-referencing. 

Plans for prototypes and implementations live in the docs/plans subdirectory. 

Scripts used for exploring the dataset should be saved to the scripts subdirectory and should contain the date in the filename. **Prefer scripts to ad-hoc bash commands.**  If using python, always run scripts with `uv run` instead of the system python. If a script has dependencies, declare them in the script with PEP 723 style metadata: 

```
# /// script
# requires-python = ">=3.12,<3.13"
# dependencies = []
# 
# ///

```

Temporary downloads and other misc artifacts can be saved to the scratch subdirectory, which may be occasionally manually wiped by the user as needed. **Do not pollute your context window by reading from the scratch directory unnecessarily.**

## Dataset

**OMol25** is a large-scale DFT dataset at ωB97M-V/def2-TZVPD level of theory, spanning small molecules, biomolecules, metal complexes, and electrolytes. OMol-0 contains ~100M structures; OMol-1 (released 2026-01) contains ~140M. OPoly26 is a related polymer extension (~6M). We currently hold the OMol-0 4M split on Eagle but plan to maintain a full copy.

We hold the **full dataset** (including ORCA output files), not just the descriptors available on HuggingFace. This includes:

- `orca.tar.zst` — raw ORCA outputs (orca.out, orca.inp, orca.engrad, orca_property.txt, orca.xyz)
- `orca.gbw.zstd0` — Geometry-Basis-Wavefunction file (molecular orbitals, converged SCF wavefunction)
- `density_mat.npz` — upper-triangle of the density matrix (and spin density for unrestricted systems)

## Storage & Access

- **Location**: Argonne Eagle filesystem
- **Globus collection**: `0b73865a-ff20-4f57-a1d7-573d86b54624`
- **Globus URL**: <https://app.globus.org/file-manager?origin_id=0b73865a-ff20-4f57-a1d7-573d86b54624&origin_path=%2F>

Dataset is organized on Eagle by internal generation structure. To find paths for specific systems, use the ASE-DB index (train_4M.tar.gz from HuggingFace):

```python
from fairchem.core.datasets import AseDBDataset
import os

dataset = AseDBDataset({"src": "path/to/train_4M/"})
for idx in range(len(dataset)):
    atoms = dataset.get_atoms(idx)
    relative_dir = os.path.dirname(atoms.info["source"])  # matches Argonne path structure
    domain = atoms.info["data_id"]   # e.g. "elytes" — authoritative domain label, no path parsing needed
```
