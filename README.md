# cantilever-pymechanical

An automated simulation pipeline using Ansys PyMechanical to generate labeled Frequency Response Function (FRF) datasets for a thin cantilever beam. This is an active research project at Texas A&M University targeting AI-based structural damage detection.

## Project Goal

The pipeline simulates both healthy and damaged cantilever beam configurations to build a labeled training dataset for an AI model capable of detecting and localizing structural defects from FRF data. The approach is analogous to what a Polytec Scanning Laser Vibrometer would measure experimentally — but generated fully in simulation.

## Pipeline Overview

1. Import cantilever beam geometry (SolidWorks `.SLDPRT`)
2. Mesh the model with a specified element size
3. Run a modal analysis to extract natural frequencies
4. Apply a harmonic load at the beam tip across a specified frequency range
5. Extract complex nodal displacements (real + imaginary) at all nodes and frequencies
6. Simulate damage by reducing Young's modulus in a localized zone and re-solving
7. Export all results to CSV with health labels for AI training

## Files

| File | Description |
|------|-------------|
| `Test_Run_2.py` | Healthy beam simulation — imports geometry, meshes, runs modal + harmonic analysis, exports `nodal_displacement_complex.csv` |
| `damage_run.py` | Damage sweep — reads healthy baseline, applies 9 damage configurations (3 locations × 3 severities), exports `dataset.csv` |
| `Harmonic_Subfunctions.py` | All helper functions: session setup, mesh, BCs, harmonic analysis, damage material application, data export |
| `plot_frf.py` | Healthy beam FRF plots (amplitude, phase, mode shape, real/imaginary) |
| `plot_damage.py` | Healthy vs. damaged FRF comparison plots |

## Run Order

```
1. Test_Run_2.py       →  generates nodal_displacement_complex.csv + modal_frequencies.json
2. damage_run.py       →  generates dataset.csv  (reads healthy CSV as baseline)
3. plot_frf.py         →  inspect healthy FRF
4. plot_damage.py      →  compare healthy vs. damaged
```

## Outputs

All outputs are written to the `output_dir` specified in the config (default: `C:\Users\...\Documents\PyMechanical\Outputs\`).

| File | Description |
|------|-------------|
| `nodal_displacement_complex.csv` | Complex nodal displacements for the healthy beam |
| `modal_frequencies.json` | Natural frequencies from modal analysis |
| `dataset.csv` | Combined healthy + damaged labeled dataset |
| `run_healthy.csv` | Healthy baseline run (intermediate) |
| `run_dmg_loc###_sev###.csv` | Individual damage run results |

### dataset.csv schema

```
freq_Hz, node_id, x, y, z,
ux_real, ux_imag, uy_real, uy_imag, uz_real, uz_imag,
damage_location_mm, damage_severity, label
```

- `damage_location_mm`: center of damage zone along beam length (mm); `0.0` for healthy
- `damage_severity`: fraction of Young's modulus removed (e.g. `0.25` = 25% reduction); `0.0` for healthy
- `label`: `"healthy"` or `"damaged"`

## Damage Simulation

Damage is modeled as a localized stiffness reduction. For each configuration:

1. A Named Selection (`NS_DAMAGE_ELEMENTS`) is created using worksheet `GenerationCriteria` to select all mesh elements within a Z-range centered on the damage location
2. A `DamageMaterial` is built by extracting Structural Steel from `General_Materials.xml` and reducing Young's modulus (with Bulk and Shear moduli derived consistently)
3. A `MaterialAssignment` scopes `DamageMaterial` to the damage zone
4. The harmonic analysis is re-solved and results exported
5. The assignment and named selection are removed before the next configuration

### Damage sweep configuration (in `damage_run.py`)

```python
"damage_locations_frac": [0.25, 0.50, 0.75],  # fraction of beam length
"damage_severities":     [0.10, 0.25, 0.50],  # fraction of E removed
"damage_zone_frac":      0.05,                 # damage zone width (5% of beam length)
```

This produces **9 damage configurations** × 1 healthy baseline = 10 labeled FRF sets.

## Requirements

- Ansys Mechanical 2025 R2 (v252) with valid license
- Python 3.12+
- `ansys-mechanical-core==0.11.0`
- `matplotlib`
- `numpy`
- `pandas`

## Configuration

Simulation parameters are set in the `config` dictionary at the top of each script:

```python
config = {
    "geometry_path":  r"path\to\Thin_Beam.SLDPRT",
    "element_size":   1.6e-3,        # meters
    "f_start_hz":     100.0,
    "f_end_hz":       5000.0,
    "n_points":       20,
    "force_value_N":  1.0,           # harmonic tip force, Y-direction
    "output_dir":     r"path\to\Outputs",
    "show_gui":       False,         # True to open Mechanical GUI
}
```

## Known Limitations (PyMechanical 0.11.0)

- `Material.Delete()` is not available — `DamageMaterial` entries accumulate in the materials list across runs but are harmless once the `MaterialAssignment` is removed
- `Model.Materials.Import()` may create duplicate material names (`DamageMaterial (2)`, etc.) on repeat calls; the pipeline handles this by dynamically resolving the correct material name after each import
- Mesh node coordinates are returned in **mm** (not meters)
