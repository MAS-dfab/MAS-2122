import time
import os
import logging

from compas_slicer.slicers import PlanarSlicer
import compas_slicer.utilities as utils
from compas_slicer.pre_processing import move_mesh_to_point
from compas_slicer.post_processing import simplify_paths_rdp_igl
from compas_slicer.post_processing import seams_smooth
from compas_slicer.post_processing import seams_align
from compas_slicer.print_organization import PlanarPrintOrganizer
from compas_slicer.print_organization import set_extruder_toggle
from compas_slicer.print_organization import add_safety_printpoints
from compas_slicer.print_organization import set_linear_velocity_constant
from compas_slicer.print_organization import set_blend_radius
from compas_slicer.utilities import save_to_json
from compas_view2 import app

from compas.datastructures import Mesh
from compas.geometry import Point

# ==============================================================================
# Logging
# ==============================================================================
logger = logging.getLogger('logger')
logging.basicConfig(format='%(levelname)s-%(message)s', level=logging.INFO)

# ==============================================================================
# Select location of data folder and specify model to slice
# ==============================================================================
DATA = os.path.join(os.path.dirname(__file__), 'data')
OUTPUT_DIR = utils.get_output_directory(DATA)  # creates 'output' folder if it doesn't already exist
MODEL = 'distorted_a_closed_mid_res.obj'

start_time = time.time()

# ==========================================================================
# Load mesh
# ==========================================================================
compas_mesh = Mesh.from_obj(os.path.join(DATA, MODEL))

# ==========================================================================
# Move to origin
# ==========================================================================
move_mesh_to_point(compas_mesh, Point(0, 0, 0))

# ==========================================================================
# Slicing
# options: 'default': Both for open and closed paths. But slow
#          'cgal':    Very fast. Only for closed paths.
#                     Requires additional installation (compas_cgal).
# ==========================================================================
slicer = PlanarSlicer(compas_mesh, slicer_type="cgal", layer_height=10)
slicer.slice_model()

seams_align(slicer, align_with="y_axis")

# ==========================================================================
# Simplify the paths by removing points with a certain threshold
# change the threshold value to remove more or less points
# ==========================================================================
simplify_paths_rdp_igl(slicer, threshold=0.6)

# ==========================================================================
# Smooth the seams between layers
# change the smooth_distance value to achieve smoother, or more abrupt seams
# ==========================================================================
seams_smooth(slicer, smooth_distance=10)

# ==========================================================================
# Prints out the info of the slicer
# ==========================================================================
slicer.printout_info()

# ==========================================================================
# Save slicer data to JSON
# ==========================================================================
save_to_json(slicer.to_data(), OUTPUT_DIR, 'slicer_data.json')

# ==========================================================================
# Initializes the PlanarPrintOrganizer and creates PrintPoints
# ==========================================================================
print_organizer = PlanarPrintOrganizer(slicer)
print_organizer.create_printpoints(generate_mesh_normals=False)

# ==========================================================================
# Set fabrication-related parameters
# ==========================================================================
set_extruder_toggle(print_organizer, slicer) #extruder toggle
add_safety_printpoints(print_organizer, z_hop=10.0) # safety printpoints
set_linear_velocity_constant(print_organizer, v=100.0) # velocity
set_blend_radius(print_organizer, d_fillet=10.0) # blend radius

# ==========================================================================
# Prints out the info of the PrintOrganizer
# ==========================================================================
print_organizer.printout_info()

# ==========================================================================
# Converts the PrintPoints to data and saves to JSON
# =========================================================================
printpoints_data = print_organizer.output_nested_printpoints_dict()
save_to_json(printpoints_data, OUTPUT_DIR, 'out_printpoints_nested.json')

# ==========================================================================
# Initializes the compas_viewer and visualizes results
# ==========================================================================
viewer = app.App(width=1600, height=1000)
# slicer.visualize_on_viewer(viewer, visualize_mesh=False, visualize_paths=True)
print_organizer.visualize_on_viewer(viewer, visualize_printpoints=True)
viewer.show()

end_time = time.time()
print("Total elapsed time", round(end_time - start_time, 2), "seconds")
