# OMol25 4M Split — Directory Structure Analysis

*2026-03-13, derived from Paths.txt (3,986,753 paths) + Globus ls sampling + DATASET.md*

## Top-Level Taxonomy

There are 34 distinct top-level directories. These fall into four domains matching the paper, plus internal generation batches nested under `omol/`.

### Biomolecules (~795K structures)

| Directory | Count | Notes |
|---|---|---|
| `omol/solvated_protein` | 382,336 | Two output batches: `outputs_240923` (336K), `outputs_241002` (47K). Paths like `spf_NNNNNNN_charge_spin/stepN`. |
| `pdb_fragments_300K` | 93,334 | PDB-derived protein-ligand fragments at 300K. Names encode PDB ID, binding site states, ligand IDs. |
| `pdb_fragments_400K` | 92,698 | Same as above at 400K. |
| `ml_protein_interface` | 61,859 | ML-sampled protein-protein interface structures. |
| `protein_interface` | 44,972 | Protein-protein interface fragments (DIPS-Plus derived per paper). |
| `protein_core` | 35,406 | Buried protein residue environments. Names: `PDBID_coreChainResnum_charge_spin`. |
| `rna` | 34,745 | RNA structures. Names encode PDB ID, chain, frame, charge, spin. |
| `dna` | 24,647 | DNA structures. Similar naming to RNA. |
| `nakb` | 5,606 | Nucleic Acid Knowledge Base structures (non-traditional nucleic acid forms). |
| `pdb_pockets_300K` | 16,927 | Protein binding pocket environments at 300K. |
| `pdb_pockets_400K` | 3,210 | Same at 400K. |

### Metal Complexes (~865K structures)

| Directory | Count | Notes |
|---|---|---|
| `omol/metal_organics` | 537,439 | Four generation batches. `restart5to6` (364K) uses opaque job hashes. Others use `ID_charge_spin_mult/stepN` format. Includes lanthanide-specific batch (`outputs_ln_082524`, 14K). |
| `tm_react` | 158,190 | Transition metal reactivity. Richly encoded names: dataset origin (MOBH/ROST/MOR), metal+oxidation, charge, UHF, ligand SMILES, reaction step. |
| `ml_mo` | 77,603 | ML-sampled metal organics (MACE/EqV2 MD trajectories). |
| `rgd_uks` | 75,316 | Unrestricted Kohn-Sham calculations. Names: `MR_ID_charge_UHFspin_charge_spin`. |
| `low_spin_23` | 12,939 | Low-spin metal complex calculations (paper describes running lowest possible spin states). |
| `mo_hydrides` | 3,396 | Metal-hydride complexes. |

### Electrolytes (~798K structures)

| Directory | Count | Notes |
|---|---|---|
| `omol/electrolytes` | 497,630 | Three sub-batches: `solvated_090624` (303K, named by solute molecule + solvation shell), `md_based` (166K, MD-sampled ion/solvent clusters), `outputs_unsolvated_120424` (29K, bare molecules). |
| `electrolytes_reactivity` | 66,974 | Electrolyte reactivity structures. |
| `scaled_separations_exp` | 53,219 | Intermolecular distance scaling experiments (dilated clusters per paper). |
| `ml_elytes` | 51,599 | ML-sampled electrolyte structures. |
| `electrolytes_redox` | 46,081 | Redox (electron added/removed) variants. |
| `electrolytes_scaled_sep` | 30,769 | More scaled separation structures. |
| `droplet` | 18,694 | Gas-solvent interface droplet structures. |
| `rpmd` | 18,652 | Ring Polymer MD sampled structures (nuclear quantum effects). |
| `5A_elytes` | 14,202 | 5Å cutoff shell electrolyte clusters (secondary coordination shell). |

### Community / Small Molecules (~1,528K structures)

| Directory | Count | Notes |
|---|---|---|
| `ani1xbb` | 737,210 | ANI-1x backbone conformers. Largest single subdataset. |
| `ani2x` | 215,642 | ANI-2x recomputed at ωB97M-V. |
| `trans1x` | 213,731 | Transition1x reaction paths. Names encode reaction ID + frame. |
| `geom_orca6` | 199,805 | GEOM conformer dataset recomputed with ORCA 6. |
| `orbnet_denali` | 51,102 | OrbNet Denali training structures (ChEMBL conformers). |
| `pmechdb` | 49,832 | Polar mechanism reaction database. |
| `spice` | 44,450 | SPICE dataset recomputed. Names preserve original dataset/subset IDs. |
| `omol/redo_orca6` | 7,555 | Recomputed metal organics (ORCA 6 redo). |
| `omol/torsion_profiles` | 4,248 | Torsion angle scans. |
| `rmechdb` | 2,803 | Radical mechanism reaction database. |
| `noble_gas` | 1,915 | Noble gas containing systems. |
| `noble_gas_compounds` | 18 | Noble gas compound structures. |

---

## Path Structure Patterns

Paths have **variable depth** depending on provenance:

| Depth | Count | Pattern | Example |
|---|---|---|---|
| 2 | 2,557,546 | `dataset/leaf_id` | `ani1xbb/aniBB_022_163758_0_1` |
| 4 | 364,470 | `omol/domain/batch/job_hash` | `omol/metal_organics/restart5to6/job_174...` |
| 5 | 891,523 | `omol/domain/batch/system_id/stepN` | `omol/electrolytes/solvated_090624/mol_name.../step4` |
| 6 | 173,215 | `omol/domain/sub/batch/system_id/stepN` | `omol/electrolytes/md_based/outputs_241029/.../step0` |

The `atoms.info["source"]` field in the ASE-DB includes the filename suffix (e.g. `.../step3/orca.tar.zst`). `os.path.dirname(source)` gives the directory — matching the paths in Paths.txt exactly.

---

## Trailing `_charge_spin` Convention — RESOLVED

**Spin is multiplicity (2S+1)**, confirmed by the DATASET.md example: a closed-shell restricted calculation shows `charge: 0, spin: 1, unrestricted: False`. This is standard ORCA multiplicity convention, not UHF unpaired-electron count.

| Trailing pattern | Count | Meaning |
|---|---|---|
| `_0_1` | 1,480,234 | Neutral singlet (closed-shell) |
| `_1_1` | 285,746 | +1 charge, singlet |
| `_-1_1` | 163,968 | −1 charge, singlet |
| `_2_1` | 56,265 | +2 charge, singlet |
| `_0_3` | 51,271 | Neutral triplet |
| `_-2_1` | 49,025 | −2 charge, singlet |

Values like `_2_7` (sextet, 5 unpaired electrons) are plausible for high-spin d⁵ or f-block metals.

---

## Files Per Directory — RESOLVED

**All three files are present in every directory**, confirmed across all depth levels and domains sampled:

- `orca.tar.zst` — raw ORCA outputs bundle
- `orca.gbw.zstd0` — compressed GBW wavefunction file
- `density_mat.npz` — upper triangle of density matrix

---

## File Sizes

Sampled via `globus ls -l`. Sizes correlate strongly with system size (n_basis scales ~cubically with atom count):

| Sample | Domain | density_mat | gbw | orca.tar | Total |
|---|---|---|---|---|---|
| `solvated_protein/spf_2570544.../step0` | biomol | 183 KB | 372 KB | 267 KB | ~0.8 MB |
| `ani1xbb/aniBB_022_163758_0_1` | small mol | 2.5 MB | 5.2 MB | 2.8 MB | ~10.5 MB |
| `electrolytes/solvated.../step4` | electrolyte | 4.8 MB | 9.6 MB | 4.7 MB | ~19 MB |
| `tm_react/MOBH6_Sm3...` | metal complex | 9.8 MB | 19.5 MB | 10.4 MB | ~40 MB |
| `metal_organics/restart5to6/job_...` | metal complex | 8.8 MB | 17.7 MB | 25.8 MB | ~52 MB |
| `pdb_fragments_300K/3zpt_...` | biomol | 25.4 MB | 50.4 MB | 18.2 MB | ~94 MB |

**Pattern**: `gbw ≈ 2× density_mat` (gbw holds full MO coefficients; density is the upper triangle only). `orca.tar.zst` is the most variable — it contains text output that scales with convergence steps and output verbosity.

The solvated_protein sample is surprisingly small (~0.8 MB). This is consistent with small extracted pocket fragments, not full proteins.

**Rough order-of-magnitude estimate**: The 4M subset appears to range from sub-MB to ~100MB per structure. A ballpark average of 10–30 MB/structure implies **40–120 TB** for the 4M split in raw files. (The README says the Eagle collection holds petabytes for the full 100M dataset.)

---

## ASE-DB Metadata — RESOLVED

The ASE-DB `atoms.info` dict contains rich per-structure metadata beyond just the path:

| Field | Type | Notes |
|---|---|---|
| `source` | str | Path including filename (e.g. `.../step3/orca.tar.zst`) |
| `data_id` | str | **Domain label** — e.g. `elytes`. Resolves domain mapping without parsing paths. |
| `charge` | int | Total charge |
| `spin` | int | Spin multiplicity (2S+1) |
| `num_atoms` | int | Atom count |
| `num_electrons` | int | Electron count |
| `num_ecp_electrons` | int | ECP electrons (relevant for heavy elements) |
| `n_scf_steps` | int | SCF convergence steps |
| `n_basis` | int | Basis function count |
| `unrestricted` | bool | Restricted vs unrestricted calculation |
| `nl_energy` | float | VV10 dispersion energy (eV) |
| `integrated_densities` | array | [α, β, total] — sanity check for density |
| `homo_energy` | array | HOMO energy (eV) |
| `homo_lumo_gap` | array | HOMO-LUMO gap (eV) |
| `s_squared` | float | ⟨S²⟩ — net magnetization |
| `s_squared_dev` | float | Deviation from ideal ⟨S²⟩ |
| `warnings` | list | ORCA warning messages |
| `mulliken_charges` | array | Per-atom Mulliken charges |
| `lowdin_charges` | array | Per-atom Löwdin charges |
| `nbo_charges` | array | Per-atom NBO charges (when available) |
| `composition` | str | Composition string e.g. `B1Br1C27H36N2O16S1` |
| `mulliken_spins` | array | Per-atom spins (unrestricted only) |
| `lowdin_spins` | array | Per-atom spins (unrestricted only) |
| `nbo_spins` | array | Per-atom spins (unrestricted only) |

This is directly useful for the index build: **`data_id` replaces path-parsing for domain assignment**, and scalar fields like `num_atoms`, `charge`, `spin`, `num_electrons`, `homo_lumo_gap` are available as cheap filter columns.

---

## Implications for the Index Build

From the design plan, the parquet index needs `domain`, `subsampling`, `eagle_path`, `file_sizes`, and `has_<element>` booleans. The ASE-DB provides everything except `file_sizes`:

- `domain` ← `atoms.info["data_id"]` (no path parsing needed)
- `subsampling` ← infer from top-level directory or second path component
- `eagle_path` ← `os.path.dirname(atoms.info["source"])`
- `has_<element>` ← parse `atoms.info["composition"]` or call `atoms.get_atomic_numbers()`
- `file_sizes` ← **not in ASE-DB**, requires a separate pass (Globus or file stat)

Additional scalar columns now clearly available at zero extra cost:
`charge`, `spin`, `num_atoms`, `num_electrons`, `n_basis`, `homo_lumo_gap`, `unrestricted`, `s_squared`

---

## Remaining Open Questions

1. **`data_id` values**: We've seen `elytes`. What are the other values? (Likely `biomol`, `metal_complex`, `small_mol` or similar — need one sample per domain to confirm.)

2. **`restart5to6` job hashes**: Are chemical properties (composition, charge, spin) accessible from `atoms.info` for this batch, or are these structures not in the 4M ASE-DB index at all?

3. **File sizes at scale**: Our 6-sample survey shows order-of-magnitude variation. For accurate transfer estimation in the manifest service, do we need per-structure sizes, or is a per-domain average sufficient for the prototype?

4. **`subsampling` tag definition**: The design plan calls for a `subsampling` tag. What granularity is useful? Options: top-level dir name, `omol/` sub-batch, or `ml_*` vs hand-generated distinction.

5. **OMol-1 and OPoly26**: The Eagle collection presumably holds OMol-0 data only (the 4M split). Do OMol-1 and OPoly26 have separate Globus collections or live under the same root?
