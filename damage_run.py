from ansys.mechanical.core import launch_mechanical
import os, json

from Harmonic_Subfunctions import (
    setup_session_and_model,
    check_body_material,
    setup_mesh,
    check_model_info,
    setup_harmonic_analysis,
    add_fixed_on_support_face,
    add_nodal_force,
    select_node_by_id,
    get_top_face_nodes,
    solve_model,
    export_complex_displacement,
    close_mechanical,
    apply_damage_apdl,
    remove_damage_apdl,
    append_to_dataset,
)

if __name__ == "__main__":
    config = {
        # ── Geometry ──────────────────────────────────────────────────────────
        "geometry_path": r"C:\Users\coetech\OneDrive - Texas A&M University\Research\PyMechanical\Thin_beam\Thin_Beam.SLDPRT",

        # ── Mesh ──────────────────────────────────────────────────────────────
        "element_size": 1.6e-3,          # meters

        # ── Harmonic analysis ─────────────────────────────────────────────────
        "f_start_hz": 100.0,
        "f_end_hz":   5000.0,
        "n_points":   20,

        # ── Force ─────────────────────────────────────────────────────────────
        "force_value_N":          1.0,
        "remote_named_selection": "FORCE_NODE",

        # ── GUI ───────────────────────────────────────────────────────────────
        "show_gui": True,               # headless for batch dataset generation

        # ── Output ────────────────────────────────────────────────────────────
        "output_dir": r"C:\Users\coetech\Documents\PyMechanical\Outputs",
        "csv_name":   "run_temp.csv",

        # ── Damage sweep ──────────────────────────────────────────────────────
        "damage_zone_frac":      0.05,                # width of damage zone as fraction of beam length
        "damage_locations_frac": [0.25, 0.50, 0.75],  # damage center positions (fraction of beam length)
        "damage_severities":     [0.10, 0.25, 0.50],  # stiffness reductions (10%, 25%, 50%)
        "dataset_csv":           r"C:\Users\coetech\Documents\PyMechanical\Outputs\dataset.csv",
    }

    dataset_csv = config["dataset_csv"]

    # ── Setup (runs once) ─────────────────────────────────────────────────────
    mech = setup_session_and_model(config)
    check_body_material(config, mech)
    setup_harmonic_analysis(config, mech)
    setup_mesh(config, mech)
    check_model_info(config, mech)

    # ── Fixed support: select all nodes at z=0 ────────────────────────────────
    fix_support_script = """
import json
mesh_data = Model.Analyses[0].MeshData
all_nodes = mesh_data.Nodes
min_z = min(n.Z for n in all_nodes)
support_node_ids = [n.Id for n in all_nodes if abs(n.Z - min_z) < 1e-6]
result = json.dumps(support_node_ids)
result
"""
    out = mech.run_python_script(fix_support_script)
    support_node_ids = json.loads(out)
    print(f"Found {len(support_node_ids)} nodes on support face (z=0)")

    create_support_ns_script = f"""
from Ansys.ACT.Interfaces.Common import SelectionTypeEnum
model = Model
mesh_data = model.Analyses[0].MeshData
selection_manager = ExtAPI.SelectionManager
sel_info = selection_manager.CreateSelectionInfo(SelectionTypeEnum.MeshNodes)
sel_info.Ids = {support_node_ids}
selection_manager.ClearSelection()
selection_manager.NewSelection(sel_info)

ns_container = model.NamedSelections
if ns_container is None:
    dummy = model.AddNamedSelection()
    dummy.Delete()
    ns_container = model.NamedSelections

for ns in list(ns_container.Children):
    if ns.Name == "NS_SUPPORT_FACE":
        ns.Delete()

ns = model.AddNamedSelection()
ns.Name = "NS_SUPPORT_FACE"
ns.Location = sel_info
ns.Generate()
result = "OK: NS_SUPPORT_FACE created with " + str(len(support_node_ids)) + " nodes"
result
"""
    out = mech.run_python_script(create_support_ns_script)
    print("Mechanical says (support NS):", out)
    add_fixed_on_support_face(config, mech)

    # ── Pick tip node (max Z on top face) ─────────────────────────────────────
    top_nodes = get_top_face_nodes(mech)

    find_tip_script = f"""
import json
mesh_data = Model.Analyses[0].MeshData
node_ids = {top_nodes}
tip_node_id = max(node_ids, key=lambda nid: mesh_data.NodeById(nid).Z)
tip_node = mesh_data.NodeById(tip_node_id)
result = json.dumps({{"id": tip_node_id, "x": tip_node.X, "y": tip_node.Y, "z": tip_node.Z}})
result
"""
    out = mech.run_python_script(find_tip_script)
    tip_info = json.loads(out)
    tip_node_id = tip_info["id"]
    print(f"Tip node: ID={tip_node_id}, Z={tip_info['z']:.6f} m")

    select_node_by_id(mech, tip_node_id, "FORCE_NODE")
    add_nodal_force(config, mech)

    # ── Append healthy baseline from existing Test_Run_2 output ───────────────
    healthy_csv = "nodal_displacement_complex.csv"
    healthy_path = os.path.join(config["output_dir"], healthy_csv)
    if not os.path.exists(healthy_path):
        raise FileNotFoundError(
            f"Healthy baseline not found: {healthy_path}\n"
            "Run Test_Run_2.py first to generate the healthy beam data."
        )
    print(f"\nUsing existing healthy baseline: {healthy_path}")
    append_to_dataset(config, healthy_csv, dataset_csv,
                      damage_location_mm=0.0, damage_severity=0.0, label="healthy")

    # ── Damage sweep ──────────────────────────────────────────────────────────
    for loc_frac in config["damage_locations_frac"]:
        for severity in config["damage_severities"]:
            print(f"\n=== Damage: location={loc_frac:.0%} of beam, severity={severity:.0%} ===")
            config["damage_location_frac"] = loc_frac
            config["damage_severity"]      = severity

            # Apply damage BEFORE solving
            info = apply_damage_apdl(config, mech)

            temp_csv = f"run_dmg_loc{int(loc_frac * 100):03d}_sev{int(severity * 100):03d}.csv"
            config["csv_name"] = temp_csv
            solve_model(config, mech)
            export_complex_displacement(config, mech)
            append_to_dataset(config, temp_csv, dataset_csv,
                              damage_location_mm=info["damage_center_mm"],
                              damage_severity=severity,
                              label="damaged")

            remove_damage_apdl(mech)

    print(f"\nDataset generation complete. Output: {dataset_csv}")

    # ── Inspect in Mechanical GUI before closing ──────────────────────────────
    input("Press Enter to close Mechanical when you are done inspecting...")

    # ── Close ─────────────────────────────────────────────────────────────────
    close_mechanical(config, mech)
