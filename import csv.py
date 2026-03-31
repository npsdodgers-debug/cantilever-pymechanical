import csv
import math
import matplotlib.pyplot as plt
import numpy as np
import os

# =============================================================================
# Load CSV
# =============================================================================
csv_path = r"C:\Users\coetech\Documents\PyMechanical\Outputs\nodal_displacement_complex.csv"
out_dir  = r"C:\Users\coetech\Documents\PyMechanical\Thin_beam"
os.makedirs(out_dir, exist_ok=True)

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

# =============================================================================
# Pick representative nodes at different z locations
# =============================================================================
# Build z -> node_id map (one node per z location)
z_node_map = {}
for r in rows:
    if r["z"] not in z_node_map:
        z_node_map[r["z"]] = r["node_id"]

z_vals = sorted(z_node_map.keys())

# Pick 6 evenly spaced z locations (excluding z=0 fixed support)
z_free = [z for z in z_vals if z > 0]
indices = np.linspace(0, len(z_free) - 1, 6, dtype=int)
selected_z = [z_free[i] for i in indices]
selected_nodes = [z_node_map[z] for z in selected_z]

print("Plotting FRFs for nodes:")
for z, nid in zip(selected_z, selected_nodes):
    print(f"  Node {nid} at z={z:.1f} mm")

# =============================================================================
# Build FRF data per node
# =============================================================================
def get_frf(node_id, rows):
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
# Plot 1: FRF Amplitude vs Frequency for selected nodes
# =============================================================================
fig, ax = plt.subplots(figsize=(10, 6))
for z, nid in zip(selected_z, selected_nodes):
    freqs, amp, _, _, _ = get_frf(nid, rows)
    ax.plot(freqs, amp, marker="o", label=f"z={z:.1f} mm (node {nid})")

ax.set_xlabel("Frequency (Hz)")
ax.set_ylabel("Displacement Amplitude |uy| (mm)")
ax.set_title("FRF Amplitude - Y Displacement vs Frequency\n(Force at tip, z=203.2 mm)")
ax.legend()
ax.grid(True)
plt.tight_layout()
plt.savefig(os.path.join(out_dir, "FRF_amplitude.png"), dpi=150)
plt.show()
print("Saved: FRF_amplitude.png")

# =============================================================================
# Plot 2: Real and Imaginary parts vs Frequency for tip node
# =============================================================================
tip_node = z_node_map[max(z_vals)]
freqs, amp, phase, real, imag = get_frf(tip_node, rows)

fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

axes[0].plot(freqs, real, marker="o", color="blue", label="Real")
axes[0].plot(freqs, imag, marker="s", color="red", label="Imaginary")
axes[0].set_ylabel("Displacement (mm)")
axes[0].set_title(f"FRF Real & Imaginary Parts - Tip Node {tip_node} (z={max(z_vals):.1f} mm)")
axes[0].legend()
axes[0].grid(True)

axes[1].plot(freqs, amp, marker="o", color="green", label="Amplitude")
axes[1].set_xlabel("Frequency (Hz)")
axes[1].set_ylabel("Amplitude |uy| (mm)")
axes[1].legend()
axes[1].grid(True)

plt.tight_layout()
plt.savefig(os.path.join(out_dir, "FRF_tip_real_imag.png"), dpi=150)
plt.show()
print("Saved: FRF_tip_real_imag.png")

# =============================================================================
# Plot 3: Phase vs Frequency for selected nodes
# =============================================================================
fig, ax = plt.subplots(figsize=(10, 6))
for z, nid in zip(selected_z, selected_nodes):
    freqs, _, phase, _, _ = get_frf(nid, rows)
    ax.plot(freqs, phase, marker="o", label=f"z={z:.1f} mm (node {nid})")

ax.set_xlabel("Frequency (Hz)")
ax.set_ylabel("Phase (degrees)")
ax.set_title("FRF Phase vs Frequency")
ax.legend()
ax.grid(True)
plt.tight_layout()
plt.savefig(os.path.join(out_dir, "FRF_phase.png"), dpi=150)
plt.show()
print("Saved: FRF_phase.png")

# =============================================================================
# Plot 4: Mode shape - uy amplitude along beam at each frequency
# =============================================================================
freqs_unique = sorted(set(r["freq_Hz"] for r in rows))

# Get one node per z, sorted by z (exclude z=0)
z_sorted = sorted([z for z in z_vals if z > 0])
nodes_sorted = [z_node_map[z] for z in z_sorted]

fig, ax = plt.subplots(figsize=(10, 6))
for freq in freqs_unique:
    freq_rows = {r["node_id"]: r for r in rows if r["freq_Hz"] == freq}
    amps = []
    zs   = []
    for z, nid in zip(z_sorted, nodes_sorted):
        if nid in freq_rows:
            r = freq_rows[nid]
            amps.append(math.sqrt(r["uy_real"]**2 + r["uy_imag"]**2))
            zs.append(z)
    ax.plot(zs, amps, marker=".", label=f"{freq:.0f} Hz")

ax.set_xlabel("Z position along beam (mm)")
ax.set_ylabel("Displacement Amplitude |uy| (mm)")
ax.set_title("Spatial FRF - Displacement Shape Along Beam at Each Frequency")
ax.legend()
ax.grid(True)
plt.tight_layout()
plt.savefig(os.path.join(out_dir, "FRF_mode_shape.png"), dpi=150)
plt.show()
print("Saved: FRF_mode_shape.png")

print(f"\nAll plots saved to {out_dir}")