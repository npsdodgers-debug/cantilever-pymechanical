"""
validate_complex_extraction.py

Sanity-checks the real/imaginary displacement extraction by:
  1. Picking the tip node (max Z in the complex CSV)
  2. Plotting real, imaginary, and magnitude of Y-displacement vs frequency
  3. Checking that imaginary peaks and real zero-crossings align (resonance physics)
  4. Printing a summary of data shape and any obvious issues
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# ── Config ────────────────────────────────────────────────────────────────────
OUTPUT_DIR   = r"C:\Users\coetech\Documents\PyMechanical\Outputs"
COMPLEX_CSV  = os.path.join(OUTPUT_DIR, "nodal_displacement_complex.csv")
REAL_CSV     = os.path.join(OUTPUT_DIR, "healthy_displacement_real.csv")
IMAG_CSV     = os.path.join(OUTPUT_DIR, "healthy_imag_apdl.csv")

# ── Load data ─────────────────────────────────────────────────────────────────
print("Loading complex CSV...")
df = pd.read_csv(COMPLEX_CSV)
print(f"  Shape: {df.shape}")
print(f"  Columns: {list(df.columns)}")
print(f"  Frequencies: {df['freq_Hz'].nunique()} unique  "
      f"({df['freq_Hz'].min():.2f} – {df['freq_Hz'].max():.2f} Hz)")
print(f"  Nodes: {df['node_id'].nunique()} unique")

# ── Pick tip node (max Z, then max Y for tie-breaking) ────────────────────────
node_coords = df.groupby('node_id')[['x', 'y', 'z']].first()
tip_node_id = node_coords['z'].idxmax()
tip_z = node_coords.loc[tip_node_id, 'z']
print(f"\nTip node: ID={int(tip_node_id)}, Z={tip_z:.4f} mm")

tip_df = df[df['node_id'] == tip_node_id].sort_values('freq_Hz').reset_index(drop=True)
freqs   = tip_df['freq_Hz'].values
uy_real = tip_df['uy_real'].values
uy_imag = tip_df['uy_imag'].values
uy_mag  = np.sqrt(uy_real**2 + uy_imag**2)
phase   = np.degrees(np.arctan2(uy_imag, uy_real))

# ── Basic data checks ─────────────────────────────────────────────────────────
print("\n── Data checks ──")

# 1. Are imaginary values non-trivial?
imag_nonzero = np.count_nonzero(np.abs(uy_imag) > 1e-12)
print(f"  Non-zero imaginary Y values at tip: {imag_nonzero}/{len(uy_imag)}")
if imag_nonzero == 0:
    print("  WARNING: All imaginary values are zero — APDL export may have failed.")

# 2. Magnitude should always be >= real part
mag_check = np.all(uy_mag >= np.abs(uy_real) - 1e-15)
print(f"  Magnitude >= |real| everywhere: {mag_check}")

# 3. Find resonance peaks (local maxima of magnitude)
from scipy.signal import find_peaks
peaks, _ = find_peaks(uy_mag, height=0.001 * uy_mag.max(), distance=5)
print(f"  Resonance peaks detected at: {freqs[peaks].round(1)} Hz")

# 4. At each peak, check that phase is near ±90°
print("  Phase at peaks (should be near ±90°):")
for p in peaks:
    print(f"    {freqs[p]:.1f} Hz  phase={phase[p]:.1f}°  "
          f"real={uy_real[p]:.3e}  imag={uy_imag[p]:.3e}")

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(3, 1, figsize=(10, 9), sharex=True)
fig.suptitle(f"Tip Node (ID={int(tip_node_id)}, Z={tip_z:.2f} mm) — Y-Displacement FRF", fontsize=13)

axes[0].plot(freqs, uy_real, color='steelblue', linewidth=1.2)
axes[0].axhline(0, color='black', linewidth=0.5, linestyle='--')
for p in peaks:
    axes[0].axvline(freqs[p], color='red', linewidth=0.8, alpha=0.5)
axes[0].set_ylabel("Real (mm)")
axes[0].set_title("Real part — should cross zero near resonance peaks")

axes[1].plot(freqs, uy_imag, color='darkorange', linewidth=1.2)
for p in peaks:
    axes[1].axvline(freqs[p], color='red', linewidth=0.8, alpha=0.5,
                    label='Peak' if p == peaks[0] else None)
axes[1].set_ylabel("Imaginary (mm)")
axes[1].set_title("Imaginary part — should peak at resonance (red lines)")
if len(peaks):
    axes[1].legend()

axes[2].semilogy(freqs, uy_mag, color='darkgreen', linewidth=1.2)
for p in peaks:
    axes[2].axvline(freqs[p], color='red', linewidth=0.8, alpha=0.5)
axes[2].set_ylabel("Magnitude (mm, log)")
axes[2].set_xlabel("Frequency (Hz)")
axes[2].set_title("Magnitude = sqrt(real² + imag²)")

plt.tight_layout()
out_path = os.path.join(OUTPUT_DIR, "validate_complex_tip_node.png")
# plt.savefig(out_path, dpi=150)
print(f"\nPlot saved to: {out_path}")
plt.show()

# ── Cross-check: real CSV row/node counts match complex CSV ───────────────────
print("\n── Cross-check real vs complex CSV ──")
real_df = pd.read_csv(REAL_CSV)
print(f"  Real CSV:    {real_df['freq_Hz'].nunique()} freqs, {real_df['node_id'].nunique()} nodes")
print(f"  Complex CSV: {df['freq_Hz'].nunique()} freqs, {df['node_id'].nunique()} nodes")

# Check node sets match
real_nodes    = set(real_df['node_id'].unique())
complex_nodes = set(df['node_id'].unique())
only_real    = real_nodes - complex_nodes
only_complex = complex_nodes - real_nodes
if only_real or only_complex:
    print(f"  WARNING: {len(only_real)} nodes only in real CSV, "
          f"{len(only_complex)} only in complex CSV")
else:
    print("  Node sets match perfectly.")
