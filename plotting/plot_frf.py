import csv
import json
import math
import matplotlib.pyplot as plt
import numpy as np
import os

# =============================================================================
# Config
# =============================================================================
csv_path = r"C:\Users\coetech\Documents\PyMechanical\Outputs\nodal_displacement_complex.csv"
out_dir  = r"C:\Users\coetech\Documents\PyMechanical\Outputs"
os.makedirs(out_dir, exist_ok=True)

# =============================================================================
# Load CSV
# =============================================================================
rows = []
with open(csv_path, newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append({
            "freq_Hz":  float(row["freq_Hz"]),
            "node_id":  int(row["node_id"]),
            "x":        float(row["x"]),
            "y":        float(row["y"]),
            "z":        float(row["z"]),
            "uy_real":  float(row["uy_real"]),
            "uy_imag":  float(row["uy_imag"]),
        })

print(f"Loaded {len(rows)} rows from {csv_path}")

# =============================================================================
# Pick representative nodes along the beam (one per z-slice, near neutral axis)
# =============================================================================
all_x = [r["x"] for r in rows]
all_y = [r["y"] for r in rows]
cx = (max(all_x) + min(all_x)) / 2
cy = (max(all_y) + min(all_y)) / 2

z_node_map = {}
for r in rows:
    z = r["z"]
    dist = (r["x"] - cx)**2 + (r["y"] - cy)**2
    if z not in z_node_map or dist < z_node_map[z][1]:
        z_node_map[z] = (r["node_id"], dist)
z_node_map = {z: nid for z, (nid, _) in z_node_map.items()}

z_vals  = sorted(z_node_map.keys())
z_free  = [z for z in z_vals if z > 0]
indices = np.linspace(0, len(z_free) - 1, 6, dtype=int)
selected_z     = [z_free[i] for i in indices]
selected_nodes = [z_node_map[z] for z in selected_z]

print("Plotting FRFs for nodes:")
for z, nid in zip(selected_z, selected_nodes):
    print(f"  Node {nid} at z={z:.1f} mm")

# =============================================================================
# Helper: build FRF for a given node
# =============================================================================
def get_frf(node_id):
    node_rows = sorted(
        [r for r in rows if r["node_id"] == node_id],
        key=lambda r: r["freq_Hz"]
    )
    freqs = [r["freq_Hz"] for r in node_rows]
    amp   = [math.sqrt(r["uy_real"]**2 + r["uy_imag"]**2) for r in node_rows]
    phase = [math.degrees(math.atan2(r["uy_imag"], r["uy_real"])) for r in node_rows]
    real  = [r["uy_real"] for r in node_rows]
    imag  = [r["uy_imag"] for r in node_rows]
    return freqs, amp, phase, real, imag

# =============================================================================
# Load modal frequencies
# =============================================================================
modal_json_path = os.path.join(out_dir, "modal_frequencies.json")
modal_freqs = []
if os.path.exists(modal_json_path):
    with open(modal_json_path) as f:
        modal_freqs = json.load(f)["frequencies_hz"]
    print(f"Loaded {len(modal_freqs)} modal frequencies")
else:
    print("Warning: modal_frequencies.json not found — no resonance markers")

# =============================================================================
# Plot 1: FRF Amplitude vs Frequency
# =============================================================================
tip_node = z_node_map[max(z_vals)]
freqs_tip, amp_tip, _, _, _ = get_frf(tip_node)

fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(freqs_tip, amp_tip, marker="o", markersize=4, color="steelblue",
        linewidth=1.5, label=f"Tip node (z={max(z_vals):.1f} mm)")

# for i, mf in enumerate(modal_freqs):
#     ax.axvline(x=mf, color="gray", linestyle="--", linewidth=0.8,
#                label=f"Mode {i+1}: {mf:.1f} Hz")

ax.set_yscale("log")
ax.set_xlabel("Frequency (Hz)")
ax.set_ylabel("Displacement Amplitude |uy| (mm)")
ax.set_title("FRF Amplitude — Tip Node (Healthy Beam)")
ax.legend(fontsize=8)
ax.grid(True, which="both")
plt.tight_layout()
plt.savefig(os.path.join(out_dir, "FRF_amplitude.png"), dpi=150)
plt.show()
plt.close(fig)
print("Saved: FRF_amplitude.png")

# =============================================================================
# Plot 2: Real and Imaginary parts at tip node
# =============================================================================
tip_node = z_node_map[max(z_vals)]
freqs, amp, phase, real, imag = get_frf(tip_node)

fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
axes[0].plot(freqs, real, marker="o", markersize=3, color="steelblue", label="Real")
axes[0].plot(freqs, imag, marker="s", markersize=3, color="cornflowerblue",
             linestyle="--", label="Imaginary")
axes[0].set_ylabel("Displacement (mm)")
axes[0].set_title(f"FRF Real & Imaginary — Tip Node {tip_node} (z={max(z_vals):.1f} mm)")
axes[0].legend(fontsize=8)
axes[0].grid(True)

axes[1].plot(freqs, amp, marker="o", markersize=3, color="steelblue", label="Amplitude")
axes[1].set_xlabel("Frequency (Hz)")
axes[1].set_ylabel("Amplitude |uy| (mm)")
axes[1].legend(fontsize=8)
axes[1].grid(True)

plt.tight_layout()
plt.savefig(os.path.join(out_dir, "FRF_tip_real_imag.png"), dpi=150)
plt.show()
plt.close(fig)
print("Saved: FRF_tip_real_imag.png")

# =============================================================================
# Plot 3: Phase vs Frequency
# =============================================================================
fig, ax = plt.subplots(figsize=(10, 6))
for z, nid in zip(selected_z, selected_nodes):
    freqs, _, phase, _, _ = get_frf(nid)
    ax.plot(freqs, phase, marker="o", markersize=3, label=f"z={z:.1f} mm (node {nid})")

ax.set_xlabel("Frequency (Hz)")
ax.set_ylabel("Phase (degrees)")
ax.set_title("FRF Phase vs Frequency (Healthy Beam)")
ax.legend(fontsize=7)
ax.grid(True)
plt.tight_layout()
plt.savefig(os.path.join(out_dir, "FRF_phase.png"), dpi=150)
plt.show()
plt.close(fig)
print("Saved: FRF_phase.png")

# =============================================================================
# Plot 4: Mode shape — displacement amplitude along beam at each frequency
# =============================================================================
freqs_unique = sorted(set(r["freq_Hz"] for r in rows))
z_sorted     = sorted([z for z in z_vals if z > 0])
nodes_sorted = [z_node_map[z] for z in z_sorted]

fig, ax = plt.subplots(figsize=(10, 6))
cmap = plt.colormaps["plasma"]
for i, freq in enumerate(freqs_unique):
    color = cmap(i / max(len(freqs_unique) - 1, 1))
    freq_rows = {r["node_id"]: r for r in rows if r["freq_Hz"] == freq}
    amps, zs = [], []
    for z, nid in zip(z_sorted, nodes_sorted):
        if nid in freq_rows:
            r = freq_rows[nid]
            amps.append(math.sqrt(r["uy_real"]**2 + r["uy_imag"]**2))
            zs.append(z)
    ax.plot(zs, amps, marker=".", color=color)

sm = plt.cm.ScalarMappable(cmap=cmap,
     norm=plt.Normalize(vmin=min(freqs_unique), vmax=max(freqs_unique)))
sm.set_array([])
fig.colorbar(sm, ax=ax, label="Frequency (Hz)")

ax.set_xlabel("Z position along beam (mm)")
ax.set_ylabel("Displacement Amplitude |uy| (mm)")
ax.set_title("Spatial FRF — Displacement Shape Along Beam (Healthy Beam)")
ax.grid(True)
plt.tight_layout()
plt.savefig(os.path.join(out_dir, "FRF_mode_shape.png"), dpi=150)
plt.show()
plt.close(fig)
print("Saved: FRF_mode_shape.png")

print(f"\nAll plots saved to {out_dir}")
