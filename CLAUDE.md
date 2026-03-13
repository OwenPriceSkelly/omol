# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains miscellaneous infrastructure and analysis work for the OMol25 dataset, maintained at Argonne National Laboratory. The big-picture goal is to build tooling that makes the dataset usable for science. This repository in particular is for exploring and understanding the dataset and for quick prototyping. An explicit early goal is to build up a personal knowledge base of context for ourselves in the omol-notes subdirectory. The user will want to reference the notes as an obsidian vault, so links formatted like [[OMOL_README]] are valuable for cross-referencing. Plans for prototypes and implementations live in the docs/plans subdirectory. Scripts used for exploring the dataset should be saved to the scripts subdirectory. 

## Dataset

**OMol25** is a dataset of ~100M DFT calculations at ωB97M-V/def2-TZVPD level of theory, spanning small molecules, biomolecules, metal complexes, and electrolytes.

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
```
