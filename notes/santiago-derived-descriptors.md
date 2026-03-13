# Santiago's Derived Descriptor Layer

*2026-03-13, from email chain between Ben (ALCF), Owen, and Santiago (Sam Blau's postdoc at LBNL)*

## What This Is

Santiago has been running **Multiwfn post-processing** on the OMol25 GBW files to extract a rich set of wavefunction-derived descriptors. This is a **second data layer** on top of the raw ORCA files — not part of the original Globus collection, but being generated at LBNL and eventually destined for ALCF storage.

The post-processing is **not yet complete for all 4M structures**. Santiago notes he "only recently added the orca.out parsing" and will "eventually go back and do that for all the folders."

## Output File Structure

Each processed calculation directory gets a `generator/` subdirectory:

```
<job_folder>/
  gbw_analysis.log         — log from the Multiwfn post-processing run
  orca.inp                 — original ORCA input (used to validate post-processing succeeded)
  orca.xyz                 — geometry (present in some examples, not all)
  generator/
    bond.json              — fuzzy bond orders between all atom pairs
    qtaim.json             — QTAIM critical point analysis (per-atom + per-bond)
    orca.json              — parsed orca.out output (newer addition, not complete yet)
    charge.json            — multiple partial charge schemes per atom
    fuzzy_full.json        — Becke/Hirshfeld electron density partitioning per atom
    timings.json           — per-subroutine wall times
    other.json             — molecular-level surface descriptors (ALIE, MPP, SDP)
    out_files.zip          — raw Multiwfn output and CPprop.txt (QTAIM), kept for parser updates
```

## Schema Details

### `charge.json` — Partial Charges

Four charge schemes, each with per-atom charges plus dipole moment:
- **hirshfeld** — Hirshfeld charges + molecular dipole (xyz + magnitude)
- **adch** — ADCH charges + molecular dipole + per-atom atomic dipole moments
- **cm5** — CM5 charges + molecular dipole
- **becke** — Becke charges + molecular dipole + per-atom atomic dipole moments

Atom keys use `{index}_{element}` format, e.g. `"1_N"`, `"2_O"`.

### `bond.json` — Bond Orders

- **fuzzy_bond**: Fuzzy bond order (real-space integration) between every significantly bonded atom pair. Keys like `"1_N_to_2_O": 4.865157`. Non-bonded pairs are omitted (implicit 0).

### `qtaim.json` — QTAIM Critical Point Analysis

Keys are either atom indices (`"0"`, `"1"`, ...) for **nuclear critical points** (NCPs) or `"{i}_{j}"` for **bond critical points** (BCPs). Both share the same property schema:

| Property | Meaning |
|---|---|
| `density_all/alpha/beta` | Electron density (total, α, β spin) |
| `spin_density` | Spin density |
| `Lagrangian_K` | Lagrangian kinetic energy density |
| `Hamiltonian_K` | Hamiltonian kinetic energy density |
| `energy_density` | Total energy density |
| `lap_e_density` | Laplacian of electron density (key for bond characterization) |
| `e_loc_func` | Electron localization function (ELF) |
| `lol` | Localized orbital locator |
| `ave_loc_ion_E` | Average localized ionization energy |
| `delta_g_promolecular/hirsh` | Promolecular/Hirshfeld deformation density |
| `esp_nuc/e/total` | Electrostatic potential (nuclear, electronic, total) |
| `grad_norm/lap_norm` | Gradient/Laplacian norms |
| `eig_hess/det_hessian` | Hessian eigenvalues and determinant |
| `ellip_e_dens` | Bond ellipticity (deviation from cylindrical symmetry) |
| `eta` | Electron localizability indicator |

BCPs additionally have `connected_bond_paths` listing the two NCP indices they connect.

### `orca.json` — Parsed ORCA Output (newer, incomplete)

| Field | Notes |
|---|---|
| `scf_cycles` | Number of SCF iterations |
| `energy_components` | Nuclear repulsion, electronic energy, etc. (hartree) |
| `scf_convergence` | Final convergence criteria values |
| `homo_eh/ev`, `lumo_eh/ev` | HOMO/LUMO energies in hartree and eV |
| `homo_lumo_gap_eh` | Gap in hartree |
| `n_electrons`, `n_orbitals` | System size |
| `mulliken_charges/loewdin_charges` | Per-atom (also in ASE-DB) |
| `loewdin_bond_orders` | Löwdin bond orders (not in ASE-DB) |
| `mayer_population/charges/bond_orders` | Mayer population analysis |
| `final_energy_eh` | Total energy in hartree |
| `scf_converged` | Boolean convergence flag |
| `gradient/gradient_norm/rms/max` | Gradient components and norms |
| `dipole_au/magnitude_au` | Dipole vector and magnitude |
| `rotational_constants_cm1` | Rotational constants |
| `quadrupole_au` | Quadrupole moment tensor |
| `total_run_time_s` | ORCA wall time |

### `fuzzy_full.json` — Fuzzy Electron Density Partitioning

Per-atom integrated electron counts from Becke and Hirshfeld partitioning, plus sum and abs_sum. Useful for sanity-checking total electron count.

### `other.json` — Molecular Surface Descriptors

| Property | Meaning |
|---|---|
| `mpp_full/heavy` | Mean polarization potential (all atoms / heavy atoms only) |
| `sdp_full/heavy` | Standard deviation of polarization |
| `ALIE_Volume` | Molecular volume (Å³) |
| `ALIE_Surface_Density` | ALIE surface density |
| `ALIE_Minimal/Maximal_value` | Min/max average localized ionization energy (eV) |
| `ALIE_Overall_surface_area` | Total molecular surface area (Å²) |
| `ALIE_Positive/Negative_surface_area` | Electrophilic/nucleophilic surface area |
| `ALIE_Overall_skewness` | Skewness of ALIE distribution |

## Processing Time

From `timings.json`, per-structure cost on a 16-core ORCA job (18-atom molecule):
- Total: ~72 seconds
- Most expensive: Becke/ADCH/CM5 charge integration (~9-12 s each), Hirshfeld (~8 s), ALIE (~12 s)
- QTAIM: ~6 s

At 72 s × 4M structures = ~330,000 CPU-hours just for the post-processing. This is a major compute effort.

## Future Plans

Santiago is considering converting all JSONs to **LMDBs keyed by calculation path** — same key convention as the ASE-DB (`atoms.info["source"]` path). This would enable fast lookup and would join cleanly with our parquet index. He described this as "much faster" for serving but needing time to finalize.

## Storage Context

Santiago has started production on **OpenActinides** (OActinides), a new dataset beyond OMol25, and is asking Ben about ALCF storage space. The derived descriptor data (JSONs or LMDBs) will need to come to ALCF — it does not currently live in the Globus collection.

## Implications for the Filter Interface

1. **New high-value filter dimensions** once this data lands: HOMO-LUMO gap, bond orders, QTAIM bond characterization (e.g. covalent vs. ionic character from Laplacian sign), ALIE surface properties (electrophilicity/reactivity proxy), molecular volume.

2. **The LMDB-keyed-by-path structure** joins directly onto our parquet index — same path key. No schema change needed, just an optional join.

3. **Partial coverage is a real constraint** — the descriptor layer won't cover all 4M at launch. The filter interface should handle `null` gracefully for descriptor fields.

4. **orca.json partially overlaps ASE-DB** — HOMO energy, LUMO, gap, Mulliken/Löwdin charges are already in `atoms.info`. Mayer charges/bond orders and energy components are new.

5. **The `out_files.zip` inside each `generator/`** contains raw Multiwfn output that could be re-parsed if the parsers are updated — this is Santiago's own reproducibility hedge.
