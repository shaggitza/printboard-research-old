from solid import *
from solid.utils import *

from libs.switches import gamdias_lp as switch
from libs.controllers import tinys2 as controller
from libs import printboard
SEGMENTS=50

layout = {
    "name": "prototype",
    "type":"split",
    "controller_placement": [("right", "top"), ("left", "top")],
    "keys": [(3, 5)],
    "thumb_cluster_layout": [(1, 3)],
    "thumb_cluster_angle": 30,
    "row_angle": [(5, 5, 5, 5, 5)]
}





# for part in printboard.create_keyboard():
    # scad_render_to_file(part.shape, '{layout[name]}_{part[name]}.scad',file_header=f'$fn = {SEGMENTS};')