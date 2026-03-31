from ansys.mechanical.core import launch_mechanical  # pyMechanical
import os
import shutil
import textwrap

# =============================================================================
#
# =============================================================================

def setup_session_and_model(config):
    geometry_path = config["geometry_path"]

    mechanical = launch_mechanical(batch=False)
    proj_dir = mechanical.project_directory

    source_geom = geometry_path
    target_geom = os.path.join(proj_dir, os.path.basename(source_geom))
    if not os.path.exists(target_geom):
        shutil.copy(source_geom, target_geom)

    script = textwrap.dedent(
        f"""
        from Ansys.Mechanical.DataModel.Enums import DataModelObjectCategory, GeometryImportPreference
        from Ansys.ACT.Mechanical.Utilities import GeometryImportPreferences

        model = Model

        geom_import = model.GeometryImportGroup.AddGeometryImport()
        geom_prefs = GeometryImportPreferences()
        geom_prefs.ProcessNamedSelections = True
        geom_format = GeometryImportPreference.Format.Automatic
        geom_import.Import(r"{target_geom}", geom_format, geom_prefs)

        bodies = model.GetChildren(DataModelObjectCategory.Body, True)
        result = "OK: bodies = " + str(bodies.Count)
        result
        """
    )

    out = mechanical.run_python_script(script)
    print("Mechanical says (common):", out)
    return mechanical

# =============================================================================
#
# =============================================================================

def check_body_material(config, mechanical):
    """
    Query and print the material assigned to the first body.
    """
    script = """
from Ansys.Mechanical.DataModel.Enums import DataModelObjectCategory

bodies = Model.GetChildren(DataModelObjectCategory.Body, True)
if bodies.Count == 0:
    result = "No bodies found"
else:
    body = bodies[0]
    mat_name = str(body.Material)
    result = "Body 0 material = " + mat_name
result
"""
    out = mechanical.run_python_script(script)
    print("Mechanical says (material check):", out)

# =============================================================================
#
# =============================================================================

def setup_mesh(config, mechanical):
    element_size = config["element_size"]

    script = f"""
from Ansys.Mechanical.DataModel.Enums import DataModelObjectCategory

model = Model
mesh = model.Mesh
mesh.ElementSize = Quantity("{element_size} [m]")
mesh.GenerateMesh()

if model.Analyses.Count > 0:
    mesh_data = model.Analyses[0].MeshData
    elem_count = mesh_data.ElementCount
    node_count = mesh_data.NodeCount
    result = "OK: mesh generated with element size = {element_size} m, elements=" + str(elem_count) + ", nodes=" + str(node_count)
else:
    result = "OK: mesh generated with element size = {element_size} m (no analyses yet)"

result
"""
    out = mechanical.run_python_script(script)
    print("Mechanical says (mesh):", out)

# =============================================================================
#
# =============================================================================

def save_project(config, mechanical):
    """
    Save the current Mechanical project to the given folder, overwriting if it exists.
    """
    out_dir = config.get("output_dir", r"C:\Users\coetech\Documents\PyMechanical\Outputs")
    base_name = config.get("project_name", "cantilever_harmonic")

    script = f"""
import os
import glob

out_dir = r"{out_dir}"
base_name = r"{base_name}"

if not os.path.exists(out_dir):
    os.makedirs(out_dir)

pattern = os.path.join(out_dir, base_name + "*")
for f in glob.glob(pattern):
    try:
        os.remove(f)
    except Exception:
        pass

full_path = os.path.join(out_dir, base_name + ".mechdb")
ExtAPI.DataModel.Project.SaveAs(full_path)

"OK: project saved to " + full_path
"""
    out = mechanical.run_python_script(script)
    print("Mechanical says (save):", out)

# =============================================================================
#
# =============================================================================

def close_mechanical(config, mechanical):
    mechanical.exit(force=True)

# =============================================================================
#
# =============================================================================

def check_model_info(config, mechanical):
    """
    Print basic info: body, element, and node counts.
    """
    script = """
from Ansys.Mechanical.DataModel.Enums import DataModelObjectCategory

model = Model
bodies = model.GetChildren(DataModelObjectCategory.Body, True)
body_count = bodies.Count

if model.Analyses.Count == 0:
    result = "bodies=" + str(body_count) + ", elements=0, nodes=0 (no analyses found)"
else:
    mesh_data = model.Analyses[0].MeshData
    elem_count = mesh_data.ElementCount
    node_count = mesh_data.NodeCount
    result = "bodies=" + str(body_count) + ", elements=" + str(elem_count) + ", nodes=" + str(node_count)

result
"""
    out = mechanical.run_python_script(script)
    print("Mechanical says (info):", out)

# =============================================================================
#
# =============================================================================

def export_geometry_image(config, mechanical):
    out_dir = config.get("output_dir", r"C:\Users\coetech\Documents\PyMechanical\Outputs")
    img_name = config.get("image_name", "model_view.png")

    script = f"""
import os

out_dir = r"{out_dir}"
img_name = r"{img_name}"

if not os.path.exists(out_dir):
    os.makedirs(out_dir)

full_path = os.path.join(out_dir, img_name)

model = Model
mesh = model.Mesh
mesh.ElementSize = mesh.ElementSize
mesh.GenerateMesh()

Graphics = ExtAPI.Graphics
Graphics.Camera.SetFit()
Graphics.ExportImage(full_path)

"OK: image exported to " + full_path
"""
    out = mechanical.run_python_script(script)
    print("Mechanical says (image):", out)

# =============================================================================
#
# =============================================================================

def select_face_by_centroid_generic(mechanical, target_point, ns_name):
    script = f"""
from Ansys.ACT.Interfaces.Common import SelectionTypeEnum
import math

target = ({target_point[0]}, {target_point[1]}, {target_point[2]})

model = Model
selection_manager = ExtAPI.SelectionManager
sel_info = selection_manager.CreateSelectionInfo(SelectionTypeEnum.GeometryEntities)

closest_face = None
closest_dist = None

for assembly in ExtAPI.DataModel.GeoData.Assemblies:
    for part in assembly.AllParts:
        for body in part.Bodies:
            for face in body.Faces:
                cx, cy, cz = face.Centroid
                dx = cx - target[0]
                dy = cy - target[1]
                dz = cz - target[2]
                dist = math.sqrt(dx*dx + dy*dy + dz*dz)
                if closest_dist is None or dist < closest_dist:
                    closest_dist = dist
                    closest_face = face

if closest_face is None:
    result = "ERROR: no faces found in model"
else:
    sel_info.Entities = [closest_face]
    selection_manager.ClearSelection()
    selection_manager.NewSelection(sel_info)

    ns_container = model.NamedSelections
    if ns_container is None:
        ns_container = model.AddNamedSelection()
        ns_container.Name = "TEMP_CONTAINER"
        ns_container.Delete()
        ns_container = model.NamedSelections

    existing = []
    if ns_container is not None:
        for ns in ns_container.Children:
            if ns.Name == "{ns_name}":
                existing.append(ns)
    for ns in existing:
        ns.Delete()

    ns = model.AddNamedSelection()
    ns.Name = "{ns_name}"
    ns.Location = sel_info
    ns.Generate()

    result = "OK: {ns_name} created (closest_dist = " + str(closest_dist) + " m)"

result
"""
    out = mechanical.run_python_script(script)
    print(f"Mechanical says ({ns_name}):", out)

# =============================================================================
#
# =============================================================================

def add_nodal_force(config, mechanical):
    """
    Apply a harmonic force directly on a named selection of nodes (Y-direction).
    """
    F_amp = float(config.get("force_value_N", 1.0))
    ns_name = config.get("remote_named_selection", "FORCE_NODE")

    script = f"""
model = Model
harmonic = model.Analyses[0]
harmonic.Activate()

ns = None
for child in model.NamedSelections.Children:
    if child.Name == "{ns_name}":
        ns = child
        break

if ns is None:
    raise RuntimeError("Named selection '{ns_name}' not found")

force = harmonic.AddNodalForce()
force.Location = ns
force.XComponent.Output.DiscreteValues = [Quantity("0 [N]")]
force.YComponent.Output.DiscreteValues = [Quantity("{F_amp} [N]")]
force.ZComponent.Output.DiscreteValues = [Quantity("0 [N]")]

result = "OK: nodal force {F_amp} N (Y-direction) applied to NS '{ns_name}'"
result
"""
    out = mechanical.run_python_script(script)
    print("Mechanical says (nodal force):", out)

# =============================================================================
#
# =============================================================================

def setup_harmonic_analysis(config, mechanical):
    f_start = float(config.get("f_start_hz", 8000.0))
    f_end   = float(config.get("f_end_hz",   12000.0))
    n_steps = 10

    script = f"""
from System.Collections.Generic import List

model = Model

for a in list(model.Analyses):
    if a.Name.startswith("Harmonic"):
        a.Delete()

harmonic = model.AddHarmonicResponseAnalysis()
settings = harmonic.AnalysisSettings

settings.SolutionMethod = HarmonicMethod.Full

settings.RangeMinimum = Quantity("{f_start} [Hz]")
settings.RangeMaximum = Quantity("{f_end} [Hz]")
settings.SolutionIntervals = {n_steps}

result = "OK: harmonic reset range {f_start}-{f_end} Hz, steps={n_steps}"
result
"""
    out = mechanical.run_python_script(script)
    print("Mechanical says (harmonic setup):", out)

# =============================================================================
#
# =============================================================================

def solve_model(config, mechanical):
    script = """
analysis = Model.Analyses[0]
analysis.Solution.Solve()
result = "OK: analysis solved, status = " + str(analysis.Solution.Status)
result
"""
    out = mechanical.run_python_script(script)
    print("Mechanical says (solve):", out)

# =============================================================================
#
# =============================================================================

def add_fixed_on_support_face(config, mechanical):
    """
    Add a fixed support on the cantilever root for the harmonic analysis.
    Requires a Named Selection called 'NS_SUPPORT_FACE' on the clamped end.
    """
    script = """
from Ansys.Mechanical.DataModel.Enums import DataModelObjectCategory

model = Model

harmonic = model.Analyses[0]
harmonic.Activate()

ns = None
for n in model.NamedSelections.Children:
    if n.Name == "NS_SUPPORT_FACE":
        ns = n
        break

if ns is None:
    raise RuntimeError("Named selection 'NS_SUPPORT_FACE' not found")

fixed = harmonic.AddFixedSupport()
fixed.Location = ns

result = "OK: fixed support applied to NS_SUPPORT_FACE in harmonic analysis"
result
"""
    out = mechanical.run_python_script(script)
    print("Mechanical says (fixed support):", out)

# =============================================================================
#
# =============================================================================

def export_bc_view(config, mechanical):
    """
    Activate the analysis (with BC symbols visible) and export an image.
    """
    out_dir = config.get("output_dir", r"C:\Users\coetech\Documents\PyMechanical\Outputs")
    img_name = config.get("bc_image_name", "bc_view.png")

    script = f"""
import os

out_dir = r"{out_dir}"
img_name = r"{img_name}"

if not os.path.exists(out_dir):
    os.makedirs(out_dir)

full_path = os.path.join(out_dir, img_name)

analysis = Model.Analyses[0]
analysis.Activate()

Graphics = ExtAPI.Graphics
Graphics.Camera.SetFit()
Graphics.ExportImage(full_path)

"OK: BC view image exported to " + full_path
"""
    out = mechanical.run_python_script(script)
    print("Mechanical says (BC view):", out)

# =============================================================================
#
# =============================================================================

def print_solve_output(mechanical):
    """
    Print the tail of the Mechanical solve output file (solve.out).
    """
    script = """
import os

analysis = Model.Analyses[0]
solve_dir = analysis.WorkingDir
solve_out = os.path.join(solve_dir, "solve.out")

if os.path.isfile(solve_out):
    with open(solve_out, "r") as f:
        lines = f.readlines()
    tail = "".join(lines[-50:])
    result = tail
else:
    result = "No solve.out file found in " + str(solve_dir)

result
"""
    out = mechanical.run_python_script(script)
    print("=== solve.out tail ===")
    print(out)

# =============================================================================
#
# =============================================================================

def export_complex_displacement(config, mechanical):
    """
    Export complex nodal displacements at every harmonic frequency to a CSV.
    In Ansys harmonic results, real and imaginary parts are stored as separate
    consecutive sets: set 2k-1 = real, set 2k = imaginary for frequency k.
    One row per (frequency, node):
      freq_Hz,node_id,x,y,z,ux_real,ux_imag,uy_real,uy_imag,uz_real,uz_imag
    """
    script = r"""
def extract_all_freq_nodal_displacement(analysis, out_dir, csv_name):
    import mech_dpf
    import Ans.DataProcessing as dpf
    import os

    def get_field_data(dataSource, set_id):
        time_scoping = dpf.Scoping()
        time_scoping.Location = ""
        time_scoping.Ids = [set_id]
        u_op = dpf.operators.result.displacement()
        u_op.inputs.data_sources.Connect(dataSource)
        u_op.inputs.time_scoping.Connect(time_scoping)
        u_fc = u_op.outputs.fields_container.GetData()
        if not u_fc:
            return None, None
        u_field = u_fc[0]
        if not hasattr(u_field, "Scoping") or not hasattr(u_field, "Data"):
            return None, None
        return u_field.Scoping.Ids, u_field.Data

    try:
        mech_dpf.setExtAPI(ExtAPI)
        dataSource = dpf.DataSources(analysis.ResultFileName)

        model = dpf.Model(dataSource)
        tfs = model.TimeFreqSupport
        n_sets = tfs.NumberSets
        if n_sets == 0:
            return "ERROR: No frequency sets in result file"

        # In Ansys harmonic results, sets come in pairs:
        # odd sets = real part, even sets = imaginary part
        # Number of frequencies = n_sets / 2
        n_freqs = n_sets // 2
        freqs = [tfs.GetTimeFreq(i * 2) for i in range(n_freqs)]

        mesh_data = analysis.MeshData

        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)

        csv_path = os.path.join(out_dir, csv_name)

        with open(csv_path, "w") as f:
            f.write("freq_Hz,node_id,x,y,z,ux_real,ux_imag,uy_real,uy_imag,uz_real,uz_imag\n")

            for freq_idx in range(n_freqs):
                freq_hz = freqs[freq_idx]
                real_set = freq_idx * 2 + 1  # 1-based odd set = real
                imag_set = freq_idx * 2 + 2  # 1-based even set = imaginary

                real_ids, real_data = get_field_data(dataSource, real_set)
                imag_ids, imag_data = get_field_data(dataSource, imag_set)

                if real_ids is None:
                    continue

                # Build imaginary lookup dict for fast access
                imag_lookup = {}
                if imag_ids is not None and imag_data is not None:
                    for i, nid in enumerate(imag_ids):
                        imag_lookup[nid] = (
                            imag_data[i * 3],
                            imag_data[i * 3 + 1],
                            imag_data[i * 3 + 2],
                        )

                for i, nid in enumerate(real_ids):
                    try:
                        node = mesh_data.NodeById(nid)
                    except:
                        continue

                    ux_r = real_data[i * 3]
                    uy_r = real_data[i * 3 + 1]
                    uz_r = real_data[i * 3 + 2]

                    ux_im, uy_im, uz_im = imag_lookup.get(nid, (0.0, 0.0, 0.0))

                    f.write("{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10}\n".format(
                        freq_hz,
                        nid,
                        node.X, node.Y, node.Z,
                        ux_r, ux_im,
                        uy_r, uy_im,
                        uz_r, uz_im,
                    ))

        return "OK: complex nodal displacements exported to {}".format(csv_path)

    except Exception as e:
        return "ERROR in DPF displacement extraction: {}".format(e)

analysis = DataModel.AnalysisList[0]
out_dir = r""" + repr(config.get("output_dir", r"C:\Users\coetech\Documents\PyMechanical\Outputs")) + r"""
csv_name = r""" + repr(config.get("csv_name", "nodal_displacement_complex.csv")) + r"""
result = extract_all_freq_nodal_displacement(analysis, out_dir, csv_name)
result
"""
    out = mechanical.run_python_script(script)
    print("Mechanical says (export all freq complex displacements):", out)

# =============================================================================
#
# =============================================================================

def get_top_face_nodes(mechanical):
    """
    Returns a list of node IDs on the top face (max Y) of the beam.
    """
    script = """
import json

mesh_data = Model.Analyses[0].MeshData
all_nodes = mesh_data.Nodes

max_y = max(n.Y for n in all_nodes)
tolerance = 1e-6

top_nodes = [n.Id for n in all_nodes if abs(n.Y - max_y) < tolerance]

result = json.dumps(top_nodes)
result
"""
    out = mechanical.run_python_script(script)
    import json
    node_ids = json.loads(out)
    print(f"Found {len(node_ids)} nodes on top face")
    return node_ids

# =============================================================================
#
# =============================================================================

def select_node_by_id(mechanical, node_id, ns_name):
    """
    Create a named selection from a single node ID.
    """
    script = f"""
from Ansys.ACT.Interfaces.Common import SelectionTypeEnum

model = Model
mesh_data = model.Analyses[0].MeshData
selection_manager = ExtAPI.SelectionManager
sel_info = selection_manager.CreateSelectionInfo(SelectionTypeEnum.MeshNodes)

node = mesh_data.NodeById({node_id})
sel_info.Ids = [{node_id}]

selection_manager.ClearSelection()
selection_manager.NewSelection(sel_info)

ns_container = model.NamedSelections
for ns in list(ns_container.Children):
    if ns.Name == "{ns_name}":
        ns.Delete()

ns = model.AddNamedSelection()
ns.Name = "{ns_name}"
ns.Location = sel_info
ns.Generate()

result = "OK: NS '{ns_name}' created for node {node_id} at (" + str(node.X) + ", " + str(node.Y) + ", " + str(node.Z) + ")"
result
"""
    out = mechanical.run_python_script(script)
    print(f"Mechanical says ({ns_name}):", out)