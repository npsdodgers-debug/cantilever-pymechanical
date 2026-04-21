"""
plot_notch_comparison.py

Compares tip node FRF (magnitude + phase) between the healthy beam
and the notch-damaged beam.
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

# ── Config ────────────────────────────────────────────────────────────────────
OUTPUT_DIR = r"C:\Users\coetech\Documents\PyMechanical\Outputs"
OUT_FILE   = os.path.join(OUTPUT_DIR, "notch_comparison.png")

FREQ_MIN = 1000   # set to a number (e.g. 1000) to zoom in, None for full range
FREQ_MAX = 2000   # set to a number (e.g. 2000) to zoom in, None for full range

DATASETS = {
    "Healthy":       "nodal_displacement_complex.csv",
    "Notch damage":  "notch_displacement_complex.csv",
}
COLORS = ["steelblue", "crimson"]

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(2, 1, figsize=(11, 8), sharex=True)
fig.suptitle("Healthy vs Notch Beam FRF: Tip Node Y-displacement", fontsize=13)

for (label, fname), color in zip(DATASETS.items(), COLORS):
    path = os.path.join(OUTPUT_DIR, fname)
    df   = pd.read_csv(path)

    # Pick tip node (max Z)
    tip_id = df.groupby('node_id')['z'].first().idxmax()
    tip    = df[df['node_id'] == tip_id].sort_values('freq_Hz')
    freqs  = tip['freq_Hz'].values
    real   = tip['uy_real'].values
    imag   = tip['uy_imag'].values
    mag    = np.sqrt(real**2 + imag**2)
    phase  = np.degrees(np.arctan2(imag, real))

    # Detect peaks
    peaks, _ = find_peaks(mag, height=0.001 * mag.max(), distance=5)
    print(f"{label}: peaks at {freqs[peaks].round(1)} Hz")

    # Magnitude
    axes[0].semilogy(freqs, mag, color=color, linewidth=1.5, label=label)
    for p in peaks:
        axes[0].axvline(freqs[p], color=color, linewidth=0.7, alpha=0.4)

    # Phase
    axes[1].plot(freqs, phase, color=color, linewidth=1.5, label=label)
    for p in peaks:
        axes[1].axvline(freqs[p], color=color, linewidth=0.7, alpha=0.4)

axes[0].set_ylabel("Magnitude (mm, log)")
axes[0].set_title("Magnitude")
axes[0].legend()
axes[0].grid(True, which='both', alpha=0.3)

axes[1].set_ylabel("Phase (degrees)")
axes[1].set_xlabel("Frequency (Hz)")
axes[1].set_title("Phase")
axes[1].set_yticks([-180, -90, 0, 90, 180])
axes[1].legend()
axes[1].grid(True, which='both', alpha=0.3)

if FREQ_MIN is not None or FREQ_MAX is not None:
    axes[0].set_xlim(FREQ_MIN, FREQ_MAX)

plt.tight_layout()
# plt.savefig(OUT_FILE, dpi=150)
print(f"\nPlot saved to: {OUT_FILE}")
plt.show()
