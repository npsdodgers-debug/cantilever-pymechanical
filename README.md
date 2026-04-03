# cantilever-pymechanical

An automated simulation pipeline using Ansys PyMechanical to generate labeled Frequency Response Function (FRF) datasets for a thin cantilever beam. This is an early-stage research project.

## Project Goal

The pipeline simulates both healthy and damaged cantilever beam configurations to build a training dataset for an AI model capable of detecting and localizing structural defects. The approach is analogous to what a Polytec Scanning Laser Vibrometer would measure experimentally — but generated fully in simulation.

## Pipeline Overview

1. Import cantilever beam geometry (SolidWorks `.SLDPRT`)
2. Mesh the model with a specified element size
3. Run a modal analysis to extract natural frequencies
4. Apply a harmonic load at the beam tip across a specified frequency range
5. Extract complex nodal displacement (real + imaginary) across all nodes
6. Export results to CSV for post-processing and AI training

## Files

| File | Description |
|------|-------------|
| `Test_Run_2.py` | Main script — runs the full simulation pipeline |
| `Harmonic_Subfunctions.py` | Helper functions for mesh setup, boundary conditions, analysis, and data export |
| `plot_frf.py` | Post-processing script — loads the CSV and generates FRF plots |

## Outputs

- `nodal_displacement_complex.csv` — Complex Y-displacement at each node across the frequency sweep
- `modal_frequencies.json` — Natural frequencies from modal analysis (used for resonance markers in plots)
- `FRF_amplitude.png` — Displacement amplitude vs frequency for nodes along the beam
- `FRF_tip_real_imag.png` — Real and imaginary displacement at the tip node
- `FRF_phase.png` — Phase vs frequency for nodes along the beam
- `FRF_mode_shape.png` — Spatial displacement shape along the beam at each frequency

## Requirements

- Ansys Mechanical (licensed installation)
- Python 3.12+
- `ansys-mechanical-core`
- `matplotlib`
- `numpy`

## Configuration

All simulation parameters are set in the `config` dictionary at the top of `Test_Run_2.py`:

```python
config = {
    "geometry_path": r"path\to\Thin_Beam.SLDPRT",
    "element_size": 1.6e-3,       # meters
    "f_start_hz": 100.0,          # frequency sweep start
    "f_end_hz": 5000.0,           # frequency sweep end
    "n_points": 20,               # number of frequency points
    "force_value_N": 1.0,         # harmonic force amplitude (Y-direction)
    "output_dir": r"path\to\Outputs",
}
```
