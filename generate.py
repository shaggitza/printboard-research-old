from solid import *
from solid.utils import *

from libs.switches import gamdias_lp as switch
from libs.controllers import tinys2 as controller
from libs import printboard
from pprint import pprint

SEGMENTS=50
x = "switch"
n = "empty_switch"
layout = {
    "name": "prototype",
    "controller_placement": ("left", "top"),
    "matrixes": {
        "main": {
            "offset": (0, 0),
            "keys": [[x]*5]*3,
            # "columns_angle": [5], # moves around the bottom left corner as axys
            # "columns_stagger": [0, 10, 10, 5, 0],
            "rows_angle": None,
            # "rows_stagger": [5, 10], 
        },
        "thumb": {
            "keys":[[x]*3]*1,
            "offset": (-60, 20),
            # "column_angle":[-45, 15, 15],
            "rotation_angle": 45,
            "columns_stagger":[5, 10],
            "padding_keys": [5]
        }
    },
    "switch": switch,
    "empty_switch": printboard.empty_sw(switch),
    "controller": controller
}
pprint(layout)




for part in printboard.create_keyboard(layout):
    # print(part)
    name  = 'output/{}_{}.scad'.format(layout['name'], part['name'])
    # print(name)
    scad_render_to_file(part['shape'], name,file_header=f'$fn = {SEGMENTS};')



