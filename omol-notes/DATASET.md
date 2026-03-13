(from OMol25 huggingface repo)
# Dataset
#### LICENSE: The OMol25 dataset is provided under a CC-BY-4.0 license

OMol25 represents the largest high quality molecular DFT dataset spanning biomolecules, metal complexes, electrolytes, and community datasets.
OMol25 was generated at the ωB97M-V/def2-TZVPD level of theory. For more details on the dataset, see [arxiv](https://arxiv.org/abs/2505.08762). 

Here we provide the OMol25 training and validation splits. Dataset files are written as ase-db [`LMDBDatabase`](https://gitlab.com/ase/ase-db-backends/-/blob/main/ase_db_backends/aselmdb.py) objects. 

### Dataset splits


<table>
  <thead>
    <tr>
      <th align="center">Splits</th>
      <th align="center">Size</th>
      <th align="center">Storage</th>
      <th align="center">Download</th>
    </tr>
  </thead>
  <tbody>
    <tr><td colspan="4" align="center"><strong>OMol-0</strong></td></tr>
    <tr><td colspan="4" align="center"><em>Train</em></td></tr>
    <tr>
      <td>All</td>
      <td>101,666,280</td>
      <td>456GB</td>
      <td><a href="https://dl.fbaipublicfiles.com/opencatalystproject/data/omol/250514/train.tar.gz">train.tar.gz</a></td>
    </tr>
    <tr>
      <td>4M</td>
      <td>3,986,754</td>
      <td>19GB</td>
      <td><a href="https://dl.fbaipublicfiles.com/opencatalystproject/data/omol/250514/train_4M.tar.gz">train_4M.tar.gz</a></td>
    </tr>
    <tr>
      <td>Neutral</td>
      <td>34,335,828</td>
      <td>101GB</td>
      <td><a href="https://dl.fbaipublicfiles.com/opencatalystproject/data/omol/250514/neutral_train.tar.gz">train_neutral.tar.gz</a></td>
    </tr>
    <tr><td colspan="4" align="center"><em>Validation</em></td></tr>
    <tr>
      <td>Val</td>
      <td>2,762,021</td>
      <td>20GB</td>
      <td><a href="https://dl.fbaipublicfiles.com/opencatalystproject/data/omol/250514/val.tar.gz">val.tar.gz</a></td>
    </tr>
    <tr>
      <td>Val-neutral</td>
      <td>27,697</td>
      <td>119MB</td>
      <td><a href="https://dl.fbaipublicfiles.com/opencatalystproject/data/omol/250514/neutral_val.tar.gz">val_neutral.tar.gz</a></td>
    </tr>
    <tr><td colspan="4" align="center"><em>Test</em></td></tr>
    <tr>
      <td>Test</td>
      <td>2,805,046</td>
      <td>8GB</td>
      <td><a href="https://dl.fbaipublicfiles.com/opencatalystproject/data/omol/250514/test.tar.gz">test.tar.gz</a></td>
    </tr>
    <tr><td colspan="4" align="center"><strong>OMol-1</strong></td></tr>
    <tr><td colspan="4" align="center"><em>Train</em></td></tr>
    <tr>
      <td>All</td>
      <td>139,836,891</td>
      <td>592GB</td>
      <td><a href="https://dl.fbaipublicfiles.com/opencatalystproject/data/omol/260123/train.tar.gz">train.tar.gz</a></td>
    </tr>
  </tbody>
</table>





### Evaluation data
Input data for the OMol25 evaluations can be downloaded [🔗 here](https://dl.fbaipublicfiles.com/opencatalystproject/data/omol/250915/omol25_evaluation_inputs_250915.tar.gz).
Evaluation tasks as well as the above Val/Test splits can be submitted to the [📊 FAIR Chemistry Leaderboard](https://huggingface.co/spaces/facebook/fairchem_leaderboard).

## How to read the data

The OMol25 datasets can be accessed with the [fairchem](https://github.com/facebookresearch/fairchem) library. The package can be [installed](https://github.com/facebookresearch/fairchem#installation) with:
```
pip install git+https://github.com/facebookresearch/fairchem.git@fairchem_core-2.0.0#subdirectory=packages/fairchem-core
```

Once installed, a dataset can be read as follows
```python
from fairchem.core.datasets import AseDBDataset

dataset_path = "/path/to/omol/dir/train_4M"
dataset = AseDBDataset({"src": dataset_path})

# index the dataset to get a structure
atoms = dataset.get_atoms(0)
atomic_positions = atoms.positions
atomic_numbers = atoms.get_atomic_numbers()
```

Structures are stored as ASE [Atoms objects](https://wiki.fysik.dtu.dk/ase/ase/atoms.html). Each structure contains DFT total energy (eV) and force (eV/A) labels. Additionally, `atoms.info` contains several other properties and metadata that may be important
for model development:

`atoms.info:`

```
source: omol/electrolytes/solvated_090624/benzothiadizaole_mol1129_solv7_0_1/step3/orca.tar.zst ## Unique internal identifier
reference_source: None ## Internal identifier
data_id: elytes ## Dataset domain
charge: 0 ## Total charge
spin: 1 ## Total spin
num_atoms: 84 ## Total number of atoms
num_electrons: 396 ## Total number of electrons
num_ecp_electrons: 0 ## Total number of effective core potential electrons
n_scf_steps: 16 ## Total number of self-consistent DFT steps
n_basis: 2177 ## Number of basis functions
unrestricted: False  ## Restricted or unrestricted flag
nl_energy: 41.255288292679985 ## Dispersion energy (VV10)
integrated_densities: [197.99992624 197.99992624 395.99985248] ## Integral of the electron density, (alpha, beta, total)
homo_energy: [-8.86718388] ## HOMO energy (eV)
homo_lumo_gap: [8.31819417] ## HOMO-LUMO gap
s_squared: 0.0 ## S^2 reports on the total net magnetization (how many electrons are unpaired)
s_squared_dev: 0.0 ## Deviation of S^2 from ideal
warnings: [] ## List of DFT ORCA warning messages
mulliken_charges: [natoms x 1] ## Partial mulliken charges
lowdin_charges: [natoms x 1] ## Partial lowdin charges
nbo_charges: [natoms x 1] ## Partial nbo charges, if available
composition: B1Br1C27H36N2O16S1 ## Composition

#### if unrestrecited,
mulliken_spins: [natoms x 1] ## Partial mulliken spins
lowdin_spins: [natoms x 1] ## Partial lowdin spins
nbo_spins: [natoms x 1] ## Partial nbo spins, if available
```

## Open Polymers 2026 (OPoly26) Dataset
#### LICENSE: The OPoly26 dataset is provided under a CC-BY-4.0 license
The OPoly26 dataset is an extension of OMol25 focusing specifically on polymers. The DFT settings are identical between OMol25 and OPoly26, so the two can be mixed without worrying about inconsistencies between settings.

| Splits | Size | Storage | Download |
| :-----: | :---: | :--: | :------: |
| *Train + Val*    | 5,902,827 + 201,865   | 66GB    | [train_val.tar.gz](https://dl.fbaipublicfiles.com/opencatalystproject/data/op26/op26_train_val_260302.tar.gz)     |

## How to combine OMol25 and OPoly26
```python
from fairchem.core.datasets import AseDBDataset

omol25_path = "/path/to/omol/dir/train"
opoly26_path = "/path/to/opoly/dir/train"

dataset = AseDBDataset({"src": [omol25_path, opoly26_path]})
```