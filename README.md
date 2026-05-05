# cantilever-pymechanical

An automated simulation pipeline using Ansys PyMechanical to generate Frequency Response Function (FRF) datasets for a thin cantilever beam. Active research project at Texas A&M University.

## Project Goal

Simulate healthy and notch-damaged cantilever beam configurations and extract complex FRF data (real + imaginary displacement) for analysis.

## Beam Specifications

- **Geometry:** 203.2 mm × 6.35 mm × 0.794 mm (L × w × h), 6061 aluminum
- **Boundary condition:** Clamped at z = 0 (cantilever)
- **Loading:** 1 N harmonic force, Y-direction
- **Damping:** 1% structural damping
- **Natural frequencies (modal):** 15.7, ~98, ~275, ~540, ~892 Hz (validated against MATLAB analytical solution within ~2%)

## Repository Structure

```
simulation/
    Harmonic_Subfunctions.py    — all shared helper functions
    healthy_run.py              — healthy beam simulation
    excitation_sweep.py         — sweep force location along beam
    geometry_damage_notch.py    — damage via physical notch geometry (.stp)

plotting/
    validate_complex_extraction.py  — verify real/imaginary extraction physics
    validate_vs_matlab.py           — compare FRF peaks to MATLAB analytical solution
    plot_frf.py                     — general healthy beam FRF plotting (amplitude, phase, mode shapes)
    plot_excitation_comparison.py   — compare FRF at different excitation locations
    plot_notch_comparison.py        — healthy vs notch FRF comparison (magnitude + phase)
    plot_centerline.py              — plot centerline displacement mode shapes
    plot_notch.py                   — notch beam FRF plots (real/imag + amplitude)
```

## Run Order

```
1. healthy_run.py                →  baseline healthy beam FRF
2. excitation_sweep.py           →  FRF at multiple excitation locations
3. geometry_damage_notch.py      →  geometric notch damage FRF
```

## Imaginary Extraction Pipeline

Complex (real + imaginary) displacements are extracted using a two-step approach:

1. **Real part** — extracted via DPF (`export_real_displacement`)
2. **Imaginary part** — extracted via APDL snippet added to the solution (`add_apdl_imaginary_export`)
3. **Merge** — combined into a single complex CSV matched on node_id and nearest frequency (`merge_real_imag_csv`)

This approach was necessary because DPF in PyMechanical 0.11.0 does not reliably return both real and imaginary sets in a single call.

**Validated against MATLAB analytical solution:** peaks match within ~2% for modes 3–5. Phase at 275 Hz ≈ −89°, phase at 540 Hz ≈ −95° (both near the expected −90° at resonance).

## Excitation Location Sweep

`excitation_sweep.py` runs the harmonic analysis at multiple force locations in a single Mechanical session, outputting separate CSVs per location.

Currently configured for **50%** and **100%** of beam length. Results show distinct modal content between locations — mode 3 is near-zero at 50% excitation as expected from modal theory.

**Output files per location:**
```
healthy_exc050pct_complex.csv
healthy_exc050pct_aggregate.csv
healthy_exc050pct_centerline.csv
healthy_exc100pct_complex.csv
...
```

## Output CSV Schemas

**Complex displacement (per node, per frequency):**
```
freq_Hz, node_id, x, y, z, ux_real, uy_real, uz_real, ux_imag, uy_imag, uz_imag
```

**Aggregate FRF (one row per frequency):**
```
freq_Hz, uy_tip_real, uy_tip_imag, uy_tip_amplitude, uy_max_amplitude, uy_mean_amplitude
```

**Centerline (top face center nodes only):**
```
freq_Hz, node_id, x, y, z, ux_real, uy_real, uz_real, ux_imag, uy_imag, uz_imag
```

## Damage Simulation

**Geometric notch** (`geometry_damage_notch.py`): imports a pre-cut notch geometry (`.stp`). Confirmed Mode 1 drops from 15.7 Hz → 13.9 Hz due to stiffness reduction.

## Requirements

- Ansys Mechanical 2025 R2 (v252) with valid license
- Python 3.12+
- `ansys-mechanical-core==0.11.0`
- `matplotlib`, `numpy`, `pandas`, `scipy`

## Configuration

All scripts use a `config` dictionary:

```python
config = {
    "geometry_path":  r"path\to\Thin_Beam.SLDPRT",
    "element_size":   1.6e-3,       # meters
    "f_start_hz":     1.0,
    "f_end_hz":       1000.0,
    "n_points":       200,
    "force_value_N":  1.0,          # harmonic force amplitude, Y-direction
    "output_dir":     r"path\to\Outputs",
    "show_gui":       True,
}
```

## Known Limitations

- Mesh node coordinates are returned in **mm** (not meters)
