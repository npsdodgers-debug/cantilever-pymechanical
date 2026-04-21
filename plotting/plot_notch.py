import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# =============================================================================
# Config
# =============================================================================
out_dir  = r"C:\Users\coetech\Documents\PyMechanical\Outputs"
csv_path = os.path.join(out_dir, "notch_displacement_complex.csv")

# =============================================================================
# Load data
# =============================================================================
df = pd.read_csv(csv_path)

# Find tip node (max Z, center X, max Y)
max_y    = df["y"].max()
center_x = (df["x"].min() + df["x"].max()) / 2
tol      = 0.01

tip_candidates = df[(abs(df["y"] - max_y) < tol) & (abs(df["x"] - center_x) < tol)]
tip_node_id    = tip_candidates.loc[tip_candidates["z"].idxmax(), "node_id"]
tip_z          = tip_candidates["z"].max()
print(f"Tip node: ID={tip_node_id}, z={tip_z:.1f} mm")

tip = df[df["node_id"] == tip_node_id].sort_values("freq_Hz").copy()
tip["amplitude"] = np.sqrt(tip["uy_real"]**2 + tip["uy_imag"]**2)

# =============================================================================
# Plot 1: Real & Imaginary
# =============================================================================
fig, ax = plt.subplots(figsize=(10, 5))

ax.plot(tip["freq_Hz"], tip["uy_real"],
        marker="o", markersize=4, color="steelblue", linewidth=1.5, label="Real")
ax.plot(tip["freq_Hz"], tip["uy_imag"],
        marker="s", markersize=4, color="tomato", linewidth=1.5,
        linestyle="--", label="Imaginary")

ax.set_xlabel("Frequency (Hz)")
ax.set_ylabel("Displacement (mm)")
ax.set_title(f"FRF Real & Imaginary — Notch Beam Tip Node (z={tip_z:.1f} mm)")
ax.legend(fontsize=9)
ax.grid(True)
plt.tight_layout()
# plt.savefig(os.path.join(out_dir, "notch_frf_real_imag.png"), dpi=150)
plt.show()
plt.close(fig)
print("Saved: notch_frf_real_imag.png")

# =============================================================================
# Plot 2: Amplitude (log scale)
# =============================================================================
fig, ax = plt.subplots(figsize=(10, 5))

ax.plot(tip["freq_Hz"], tip["amplitude"],
        marker="o", markersize=4, color="steelblue", linewidth=1.5, label="Amplitude")

ax.set_yscale("log")
ax.set_xlabel("Frequency (Hz)")
ax.set_ylabel("Displacement Amplitude |uy| (mm)")
ax.set_title(f"FRF Amplitude — Notch Beam Tip Node (z={tip_z:.1f} mm)")
ax.legend(fontsize=9)
ax.grid(True, which="both")
plt.tight_layout()
# plt.savefig(os.path.join(out_dir, "notch_frf_amplitude.png"), dpi=150)
plt.show()
plt.close(fig)
print("Saved: notch_frf_amplitude.png")

print(f"\nAll plots saved to {out_dir}")
