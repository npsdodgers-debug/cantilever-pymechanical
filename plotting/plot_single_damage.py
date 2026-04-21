import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
import os
import math

# =============================================================================
# Config — update damage_csv to match whichever single_dmg file you ran
# =============================================================================
out_dir     = r"C:\Users\coetech\Documents\PyMechanical\Outputs"
healthy_csv = os.path.join(out_dir, "nodal_displacement_complex.csv")
damage_csv  = os.path.join(out_dir, "notch_displacement_complex.csv")

# =============================================================================
# Load data
# =============================================================================
h = pd.read_csv(healthy_csv)
d = pd.read_csv(damage_csv)

# Find tip node (max Z, center X, max Y)
max_y    = h["y"].max()
center_x = (h["x"].min() + h["x"].max()) / 2
tol      = 0.01

tip_candidates = h[(abs(h["y"] - max_y) < tol) & (abs(h["x"] - center_x) < tol)]
tip_node_id    = tip_candidates.loc[tip_candidates["z"].idxmax(), "node_id"]
tip_z          = tip_candidates["z"].max()
print(f"Tip node: ID={tip_node_id}, z={tip_z:.1f} mm")

# Extract tip node FRF for healthy and damaged
h_tip = h[h["node_id"] == tip_node_id].sort_values("freq_Hz")
d_tip = d[d["node_id"] == tip_node_id].sort_values("freq_Hz")

h_tip = h_tip.assign(amplitude=np.sqrt(h_tip["uy_real"]**2 + h_tip["uy_imag"]**2))
d_tip = d_tip.assign(amplitude=np.sqrt(d_tip["uy_real"]**2 + d_tip["uy_imag"]**2))

# Parse damage config from filename
damage_label = os.path.splitext(os.path.basename(damage_csv))[0].replace("single_dmg_", "").replace("_", " ")

# Load modal frequencies if available
modal_freqs = []
modal_path  = os.path.join(out_dir, "modal_frequencies.json")
if os.path.exists(modal_path):
    with open(modal_path) as f:
        modal_freqs = json.load(f)["frequencies_hz"]

# =============================================================================
# Plot 1: Amplitude — healthy vs damaged (log scale)
# =============================================================================
fig, ax = plt.subplots(figsize=(10, 6))

ax.plot(h_tip["freq_Hz"], h_tip["amplitude"],
        marker="o", markersize=4, color="steelblue",
        linewidth=1.5, label="Healthy")
ax.plot(d_tip["freq_Hz"], d_tip["amplitude"],
        marker="o", markersize=4, color="tomato",
        linewidth=1.5, linestyle="--", label=f"Damaged ({damage_label})")

ax.set_yscale("log")
ax.set_xlabel("Frequency (Hz)")
ax.set_ylabel("Displacement Amplitude |uy| (mm)")
ax.set_title(f"FRF Amplitude — Healthy vs Notch Tip Node")
ax.legend(fontsize=9)
ax.grid(True, which="both")
plt.tight_layout()
# plt.savefig(os.path.join(out_dir, "single_damage_amplitude.png"), dpi=150)
plt.show()
plt.close(fig)
print("Saved: single_damage_amplitude.png")

# =============================================================================
# Plot 2: Real & Imaginary — healthy vs damaged
# =============================================================================
fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

axes[0].plot(h_tip["freq_Hz"], h_tip["uy_real"],
             marker="o", markersize=3, color="steelblue", label="Healthy Real")
axes[0].plot(h_tip["freq_Hz"], h_tip["uy_imag"],
             marker="s", markersize=3, color="steelblue",
             linestyle="--", label="Healthy Imag")
axes[0].plot(d_tip["freq_Hz"], d_tip["uy_real"],
             marker="o", markersize=3, color="tomato", label="Damaged Real")
axes[0].plot(d_tip["freq_Hz"], d_tip["uy_imag"],
             marker="s", markersize=3, color="tomato",
             linestyle="--", label="Damaged Imag")
axes[0].set_ylabel("Displacement (mm)")
axes[0].set_title("FRF Real & Imaginary — Healthy vs Notch Tip Node")
axes[0].legend(fontsize=8)
axes[0].grid(True)

axes[1].plot(h_tip["freq_Hz"], h_tip["amplitude"],
             marker="o", markersize=3, color="steelblue", label="Healthy")
axes[1].plot(d_tip["freq_Hz"], d_tip["amplitude"],
             marker="o", markersize=3, color="tomato",
             linestyle="--", label=f"Damaged ({damage_label})")
axes[1].set_yscale("log")
axes[1].set_xlabel("Frequency (Hz)")
axes[1].set_ylabel("Amplitude |uy| (mm)")
axes[1].legend(fontsize=8)
axes[1].grid(True, which="both")

plt.tight_layout()
# plt.savefig(os.path.join(out_dir, "single_damage_real_imag.png"), dpi=150)
plt.show()
plt.close(fig)
print("Saved: single_damage_real_imag.png")

print(f"\nAll plots saved to {out_dir}")
