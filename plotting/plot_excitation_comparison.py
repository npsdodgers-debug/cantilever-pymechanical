"""
plot_excitation_comparison.py

Compares the FRF at the tip node for two excitation locations:
  - 50% of beam length (exc050pct)
  - 100% of beam length / tip (exc100pct)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

# ── Config ────────────────────────────────────────────────────────────────────
OUTPUT_DIR = r"C:\Users\coetech\Documents\PyMechanical\Outputs"
OUT_FILE   = r"C:\Users\coetech\Documents\PyMechanical\Outputs\excitation_comparison.png"

LOCATIONS = {
    "50% (101 mm)":  "healthy_exc050pct_complex.csv",
    "100% (203 mm)": "healthy_exc100pct_complex.csv",
}
COLORS = ["steelblue", "darkorange"]

# ── Load and extract tip node for each location ───────────────────────────────
fig, axes = plt.subplots(2, 1, figsize=(11, 8), sharex=True)
fig.suptitle("Healthy Beam FRF: Excitation Location Comparison", fontsize=13)

for (label, fname), color in zip(LOCATIONS.items(), COLORS):
    import os
    path = os.path.join(OUTPUT_DIR, fname)
    df   = pd.read_csv(path)

    # Pick tip node (max Z)
    tip_id = df.groupby('node_id')['z'].first().idxmax()
    tip    = df[df['node_id'] == tip_id].sort_values('freq_Hz')
    freqs  = tip['freq_Hz'].values
    real   = tip['uy_real'].values
    imag   = tip['uy_imag'].values
    mag    = np.sqrt(real**2 + imag**2)

    # Detect peaks
    peaks, _ = find_peaks(mag, height=0.001 * mag.max(), distance=5)
    print(f"{label}: peaks at {freqs[peaks].round(1)} Hz")

    phase = np.degrees(np.arctan2(imag, real))

    # Magnitude
    axes[0].semilogy(freqs, mag, color=color, linewidth=1.5, label=label)
    for p in peaks:
        axes[0].axvline(freqs[p], color=color, linewidth=0.7, alpha=0.4)

    # Phase
    axes[1].plot(freqs, phase, color=color, linewidth=1.5, label=label)
    for p in peaks:
        axes[1].axvline(freqs[p], color=color, linewidth=0.7, alpha=0.4)

axes[0].set_ylabel("Magnitude (mm, log)")
axes[0].set_title("Tip node Y-displacement magnitude")
axes[0].legend()
axes[0].grid(True, which='both', alpha=0.3)

axes[1].set_ylabel("Phase (degrees)")
axes[1].set_xlabel("Frequency (Hz)")
axes[1].set_title("Tip node Y-displacement phase")
axes[1].set_yticks([-180, -90, 0, 90, 180])
axes[1].legend()
axes[1].grid(True, which='both', alpha=0.3)

plt.tight_layout()
plt.savefig(OUT_FILE, dpi=150)
print(f"\nPlot saved to: {OUT_FILE}")
plt.show()
