"""
validate_vs_matlab.py

Compares the healthy beam FRF from PyMechanical against the MATLAB reference peaks.
Reads from the aggregate FRF CSV (tip node amplitude vs frequency).

MATLAB reference peaks (203.2 mm clamped-free beam, force and response at x=L):
    15.51, 98.05, 275.14, 538.77, 890.95 Hz
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from scipy.signal import find_peaks

# ── Config ────────────────────────────────────────────────────────────────────
OUTPUT_DIR   = r"C:\Users\coetech\Documents\PyMechanical\Outputs"
AGGREGATE_CSV = os.path.join(OUTPUT_DIR, "frf_aggregate.csv")
COMPLEX_CSV   = os.path.join(OUTPUT_DIR, "nodal_displacement_complex.csv")

MATLAB_PEAKS_HZ = [15.51, 98.05, 275.14, 538.77, 890.95]

# ── Load data ─────────────────────────────────────────────────────────────────
# Prefer the aggregate (already has tip amplitude). Fall back to complex CSV.
if os.path.exists(AGGREGATE_CSV):
    df = pd.read_csv(AGGREGATE_CSV)
    print(f"Loaded aggregate FRF: {len(df)} frequency points")
    print(f"  Range: {df['freq_Hz'].min():.2f} – {df['freq_Hz'].max():.2f} Hz")
    freqs = df['freq_Hz'].values
    amplitude = df['uy_tip_amplitude'].values
else:
    print("Aggregate CSV not found, computing from complex CSV...")
    df = pd.read_csv(COMPLEX_CSV)
    tip_node = df.groupby('node_id')['z'].first().idxmax()
    tip = df[df['node_id'] == tip_node].sort_values('freq_Hz')
    freqs = tip['freq_Hz'].values
    amplitude = np.sqrt(tip['uy_real'].values**2 + tip['uy_imag'].values**2)

# ── Warn if resolution is too coarse ─────────────────────────────────────────
spacing = np.mean(np.diff(np.sort(np.unique(freqs))))
print(f"\nFrequency resolution: ~{spacing:.1f} Hz per point")
if spacing > 30:
    print(f"  WARNING: Resolution is coarse ({spacing:.1f} Hz). Consider increasing")
    print(f"  n_points in healthy_run.py to at least 150 to resolve all peaks.")
    print(f"  The 15.51 Hz peak needs at least ~5 Hz spacing to be visible.")

# ── Detect PyMechanical peaks ─────────────────────────────────────────────────
min_height = 0.05 * np.max(amplitude)
peaks_idx, _ = find_peaks(amplitude, height=min_height, distance=3)
detected_hz = freqs[peaks_idx]

print(f"\nDetected PyMechanical peaks: {detected_hz.round(1)} Hz")
print(f"MATLAB reference peaks:      {MATLAB_PEAKS_HZ} Hz")

# ── Compare peaks ─────────────────────────────────────────────────────────────
print("\n── Peak comparison ──")
print(f"{'MATLAB (Hz)':>12}  {'PyMech (Hz)':>12}  {'Error (Hz)':>10}  {'Error (%)':>10}")
for mp in MATLAB_PEAKS_HZ:
    if len(detected_hz) == 0:
        print(f"{mp:>12.2f}  {'not detected':>12}")
        continue
    closest_idx = np.argmin(np.abs(detected_hz - mp))
    pm = detected_hz[closest_idx]
    err_hz = pm - mp
    err_pct = 100 * err_hz / mp
    flag = "  <-- good" if abs(err_pct) < 2 else ("  <-- check" if abs(err_pct) < 5 else "  <-- MISMATCH")
    print(f"{mp:>12.2f}  {pm:>12.2f}  {err_hz:>+10.2f}  {err_pct:>+9.2f}%{flag}")

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(11, 5))

ax.semilogy(freqs, amplitude, color='steelblue', linewidth=1.5, label='PyMechanical')

for i, mp in enumerate(MATLAB_PEAKS_HZ):
    ax.axvline(mp, color='red', linewidth=1.0, linestyle='--',
               label='MATLAB peaks' if i == 0 else None)
    ax.text(mp + 5, ax.get_ylim()[1] if i == 0 else amplitude.max(),
            f'{mp:.1f}', color='red', fontsize=8, va='top')

for pi in peaks_idx:
    ax.plot(freqs[pi], amplitude[pi], 'o', color='steelblue', markersize=6)

ax.set_xlabel("Frequency (Hz)")
ax.set_ylabel("|FRF| — Tip Y-displacement (mm)")
ax.set_title("Healthy Beam FRF: PyMechanical vs MATLAB reference")
ax.legend()
ax.grid(True, which='both', alpha=0.3)

plt.tight_layout()
out_path = os.path.join(OUTPUT_DIR, "validate_vs_matlab.png")
# plt.savefig(out_path, dpi=150)
print(f"\nPlot saved to: {out_path}")
plt.show()
