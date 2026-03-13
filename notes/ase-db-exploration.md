# ASE-DB Exploration Results

*3,986,754 of 3,986,754 entries scanned*

## 1. `data_id` Values

| data_id | count | % |
|---|---|---|
| `biomolecules` | 799,988 | 20.1% |
| `elytes` | 799,799 | 20.1% |
| `metal_complexes` | 797,122 | 20.0% |
| `reactivity` | 789,845 | 19.8% |
| `ani2x` | 215,642 | 5.4% |
| `trans1x` | 213,731 | 5.4% |
| `geom_orca6` | 199,805 | 5.0% |
| `rgd` | 75,316 | 1.9% |
| `orbnet_denali` | 51,102 | 1.3% |
| `spice` | 44,404 | 1.1% |

### Top-level directory → data_id mapping

| top-level dir | data_id(s) |
|---|---|
| `5A_elytes` | `elytes` |
| `ani1xbb` | `reactivity` |
| `ani2x` | `ani2x` |
| `dna` | `biomolecules` |
| `droplet` | `elytes` |
| `electrolytes_reactivity` | `elytes` |
| `electrolytes_redox` | `elytes` |
| `electrolytes_scaled_sep` | `elytes` |
| `geom_orca6` | `geom_orca6` |
| `low_spin_23` | `metal_complexes` |
| `ml_elytes` | `elytes` |
| `ml_mo` | `metal_complexes` |
| `ml_protein_interface` | `biomolecules` |
| `mo_hydrides` | `metal_complexes` |
| `nakb` | `biomolecules` |
| `noble_gas` | `elytes` |
| `noble_gas_compounds` | `elytes` |
| `omol` | `biomolecules`, `elytes`, `metal_complexes` |
| `orbnet_denali` | `orbnet_denali` |
| `pdb_fragments_300K` | `biomolecules` |
| `pdb_fragments_400K` | `biomolecules` |
| `pdb_pockets_300K` | `biomolecules` |
| `pdb_pockets_400K` | `biomolecules` |
| `pmechdb` | `reactivity` |
| `protein_core` | `biomolecules` |
| `protein_interface` | `biomolecules` |
| `rgd_uks` | `rgd` |
| `rmechdb` | `reactivity` |
| `rna` | `biomolecules` |
| `rpmd` | `elytes` |
| `scaled_separations_exp` | `elytes` |
| `spice` | `elytes`, `spice` |
| `tm_react` | `metal_complexes` |
| `trans1x` | `trans1x` |

## 2. Optimization Steps

- 1,064,738 entries have a `/stepN/` path component
- 970,214 unique parent paths contain step entries
- Steps-per-parent distribution:

| steps per parent | # parents |
|---|---|
| 1 | 885,932 |
| 2 | 75,925 |
| 3 | 6,927 |
| 4 | 1,090 |
| 5 | 262 |
| 6 | 53 |
| 7 | 18 |
| 8 | 5 |
| 10 | 1 |
| 11 | 1 |

**Sample parents and their step sets:**
- `omol/solvated_protein/outputs_240923/spf_2570544_-1_1`: steps [0]
- `omol/metal_organics/outputs_low_spin_241118/663560_11_-1_1`: steps [6]
- `omol/solvated_protein/outputs_240923/spf_2376319_0_1`: steps [1]
- `omol/electrolytes/solvated_090624/maleic_anhydride_mol653_dimer1_0_1`: steps [4]
- `omol/solvated_protein/outputs_240923/spf_1160472_-1_1`: steps [1]
- `omol/metal_organics/outputs_low_spin_241118/80013_0_1_1`: steps [2]
- `omol/metal_organics/outputs_072324/459788_2_1_1`: steps [5, 28, 36, 40, 45, 46]
- `omol/electrolytes/solvated_090624/guanidinium_mol1157_solv8_1_1`: steps [3]
- `omol/electrolytes/md_based/outputs_241029/936_F6P-1_3_shell_381_2_1`: steps [0]
- `omol/solvated_protein/outputs_240923/spf_2250832_-1_1`: steps [1]

## 3. Subsampling Tag Candidates

| subsampling tag | count | % |
|---|---|---|
| `ani1xbb` | 737,210 | 18.5% |
| `omol/metal_organics` | 537,439 | 13.5% |
| `omol/electrolytes` | 497,630 | 12.5% |
| `omol/solvated_protein` | 382,336 | 9.6% |
| `ani2x` | 215,642 | 5.4% |
| `trans1x` | 213,731 | 5.4% |
| `geom_orca6` | 199,805 | 5.0% |
| `tm_react` | 158,190 | 4.0% |
| `pdb_fragments_300K` | 93,334 | 2.3% |
| `pdb_fragments_400K` | 92,698 | 2.3% |
| `ml_mo` | 77,603 | 1.9% |
| `rgd_uks` | 75,316 | 1.9% |
| `electrolytes_reactivity` | 66,974 | 1.7% |
| `ml_protein_interface` | 61,859 | 1.6% |
| `scaled_separations_exp` | 53,219 | 1.3% |
| `ml_elytes` | 51,599 | 1.3% |
| `orbnet_denali` | 51,102 | 1.3% |
| `pmechdb` | 49,832 | 1.2% |
| `electrolytes_redox` | 46,081 | 1.2% |
| `protein_interface` | 44,972 | 1.1% |
| `spice` | 44,450 | 1.1% |
| `protein_core` | 35,406 | 0.9% |
| `rna` | 34,745 | 0.9% |
| `electrolytes_scaled_sep` | 30,769 | 0.8% |
| `dna` | 24,647 | 0.6% |
| `droplet` | 18,694 | 0.5% |
| `rpmd` | 18,652 | 0.5% |
| `pdb_pockets_300K` | 16,927 | 0.4% |
| `5A_elytes` | 14,202 | 0.4% |
| `low_spin_23` | 12,939 | 0.3% |
| `omol/redo_orca6` | 7,555 | 0.2% |
| `nakb` | 5,606 | 0.1% |
| `omol/torsion_profiles` | 4,248 | 0.1% |
| `mo_hydrides` | 3,396 | 0.1% |
| `pdb_pockets_400K` | 3,210 | 0.1% |
| `rmechdb` | 2,803 | 0.1% |
| `noble_gas` | 1,915 | 0.0% |
| `noble_gas_compounds` | 18 | 0.0% |

## 4. NBO Charge Availability

- Present: 2,680,512 (67.2%)
- Absent:  1,306,242 (32.8%)

(Run with full dataset for per-domain NBO breakdown if needed)