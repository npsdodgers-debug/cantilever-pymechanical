import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
import os

# =============================================================================
# Config
# =============================================================================
out_dir          = r"C:\Users\coetech\Documents\PyMechanical\Outputs"
centerline_path  = os.path.join(out_dir, "nodal_displacement_centerline.csv")
aggregate_path   = os.path.join(out_dir, "frf_aggregate.csv")
modal_json_path  = os.path.join(out_dir, "modal_frequencies.json")
os.makedirs(out_dir, exist_ok=True)

# =============================================================================
# Load data
# =============================================================================
cl  = pd.read_csv(centerline_path)
agg = pd.read_csv(aggregate_path)

cl["amplitude"] = np.sqrt(cl["uy_real"]**2 + cl["uy_imag"]**2)

modal_freqs = []
if os.path.exists(modal_json_path):
    with open(modal_json_path) as f:
        modal_freqs = json.load(f)["frequencies_hz"]
    print(f"Loaded {len(modal_freqs)} modal frequencies")

freqs_unique = sorted(cl["freq_Hz"].unique())
print(f"Centerline: {cl['node_id'].nunique()} nodes, {len(freqs_unique)} frequencies")
print(f"Aggregate:  {len(agg)} rows")

# =============================================================================
# Plot 1: Aggregate FRF — tip amplitude vs frequency
# =============================================================================
fig, ax = plt.subplots(figsize=(10, 5))

ax.plot(agg["freq_Hz"], agg["uy_tip_amplitude"],
        marker="o", color="steelblue", label="Tip amplitude")
ax.plot(agg["freq_Hz"], agg["uy_mean_amplitude"],
        marker="s", linestyle="--", color="cornflowerblue", label="Mean centerline amplitude")
ax.plot(agg["freq_Hz"], agg["uy_max_amplitude"],
        marker="^", linestyle=":", color="navy", label="Max centerline amplitude")

for i, mf in enumerate(modal_freqs):
    ax.axvline(x=mf, color="gray", linestyle="--", linewidth=0.8,
               label=f"Mode {i+1}: {mf:.1f} Hz" if i < 4 else None)

ax.set_xlabel("Frequency (Hz)")
ax.set_ylabel("Displacement Amplitude |uy| (mm)")
ax.set_title("Aggregate FRF — Healthy Beam")
ax.legend(fontsize=8)
ax.grid(True)
plt.tight_layout()
plt.savefig(os.path.join(out_dir, "aggregate_frf.png"), dpi=150)
plt.show()
plt.close(fig)
print("Saved: aggregate_frf.png")

# =============================================================================
# Plot 2: Aggregate FRF — real and imaginary tip components
# =============================================================================
fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

axes[0].plot(agg["freq_Hz"], agg["uy_tip_real"],
             marker="o", color="steelblue", label="Real")
axes[0].plot(agg["freq_Hz"], agg["uy_tip_imag"],
             marker="s", linestyle="--", color="cornflowerblue", label="Imaginary")
for mf in modal_freqs:
    axes[0].axvline(x=mf, color="gray", linestyle="--", linewidth=0.8)
axes[0].set_ylabel("Displacement (mm)")
axes[0].set_title("Aggregate FRF — Tip Node Real & Imaginary (Healthy Beam)")
axes[0].legend(fontsize=8)
axes[0].grid(True)

axes[1].plot(agg["freq_Hz"], agg["uy_tip_amplitude"],
             marker="o", color="steelblue", label="Amplitude")
for mf in modal_freqs:
    axes[1].axvline(x=mf, color="gray", linestyle="--", linewidth=0.8)
axes[1].set_xlabel("Frequency (Hz)")
axes[1].set_ylabel("Amplitude |uy| (mm)")
axes[1].legend(fontsize=8)
axes[1].grid(True)

plt.tight_layout()
plt.savefig(os.path.join(out_dir, "aggregate_frf_real_imag.png"), dpi=150)
plt.show()
plt.close(fig)
print("Saved: aggregate_frf_real_imag.png")

# =============================================================================
# Plot 3: Centerline mode shape — amplitude along beam at each frequency
# =============================================================================
# Use one row per Z position (mean across nodes at same Z, handles duplicates)
cl_grouped = cl.groupby(["freq_Hz", "z"])["amplitude"].mean().reset_index()

fig, ax = plt.subplots(figsize=(10, 6))
cmap = plt.colormaps["plasma"]

for i, freq in enumerate(freqs_unique):
    color = cmap(i / max(len(freqs_unique) - 1, 1))
    subset = cl_grouped[cl_grouped["freq_Hz"] == freq].sort_values("z")
    ax.plot(subset["z"], subset["amplitude"], marker=".", color=color)

sm = plt.cm.ScalarMappable(cmap=cmap,
     norm=plt.Normalize(vmin=min(freqs_unique), vmax=max(freqs_unique)))
sm.set_array([])
fig.colorbar(sm, ax=ax, label="Frequency (Hz)")

ax.set_xlabel("Z position along beam (mm)")
ax.set_ylabel("Displacement Amplitude |uy| (mm)")
ax.set_title("Centerline Mode Shape — Displacement Along Beam (Healthy Beam)")
ax.grid(True)
plt.tight_layout()
plt.savefig(os.path.join(out_dir, "centerline_mode_shape.png"), dpi=150)
plt.show()
plt.close(fig)
print("Saved: centerline_mode_shape.png")

# =============================================================================
# Plot 4: Centerline heatmap — amplitude at each (Z, frequency)
# =============================================================================
pivot = cl_grouped.pivot(index="freq_Hz", columns="z", values="amplitude")

fig, ax = plt.subplots(figsize=(12, 5))
im = ax.imshow(pivot.values, aspect="auto", origin="lower", cmap="hot",
               extent=[pivot.columns.min(), pivot.columns.max(),
                       pivot.index.min(),   pivot.index.max()])
fig.colorbar(im, ax=ax, label="Amplitude |uy| (mm)")

ax.set_xlabel("Z position along beam (mm)")
ax.set_ylabel("Frequency (Hz)")
ax.set_title("Centerline Displacement Heatmap (Healthy Beam)")
plt.tight_layout()
plt.savefig(os.path.join(out_dir, "centerline_heatmap.png"), dpi=150)
plt.show()
plt.close(fig)
print("Saved: centerline_heatmap.png")

print(f"\nAll plots saved to {out_dir}")
