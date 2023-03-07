from solid import *
from solid.utils import *

from libs.switches import gamdias_lp as switch
from libs.controllers import tinys2 as controller
from libs import printboard
from pprint import pprint

SEGMENTS=50
x = "switch"
n = "empty_switch"
tab = "1.5u"
cpsk = "1.75u"
lshift = "2.25u"
lctrl = "1.25u"
spc = "6.25u"
rctrl = "1.25u"
bksp = "2u"
backslash = "1.5u"
enter = "2.25u"
rshift = "1.75u"



sixty_five_percent = [
    [x] * 13 + [bksp] + [x], 
    [tab] + [x] * 12 + [backslash] + [x],
    [cpsk] + [x] * 11+ [enter]+ [x],
    [lshift] + [x] * 10+ [rshift] + [x] * 2,
    [lctrl] + [x] * 3+ [spc] + [x] + [rctrl] + [x] * 3,
]

layout = {
    "name": "prototype",
    "controller_placement": ("left", "top"),
    "matrixes": {
        "main": {
            "offset": (0, 0),
            "keys": [[x]*5]*3,
            "rows_angle": None,
            "columns_stagger": [0, 10, 10, 5, 0]
        },
        "thumb": {
            "keys":[[x]*3]*1,
            "offset": (-60, 20),
            # "column_angle":[-45, 15, 15],
            "rotation_angle": 30,
            "columns_stagger":[0, 5, 0],
            "padding_keys": [5, 0, 0, 0, 0]
        }
    },
    "switch": switch,
    "empty_switch": printboard.empty_sw(switch),
    "controller": controller
}

for i in range(0, 7):
    for num in [0, 0.25, 0.5, 0.75]:
        total_i = i+num
        if int(total_i) == total_i:
            total_i = int(total_i)
        layout["{}u".format(total_i)] = printboard.empty_sw(switch, body=switch.switch_body, x=18.5*total_i)
pprint(layout)



for part in printboard.create_keyboard(layout):
    # print(part)
    name  = 'output/{}_{}.scad'.format(layout['name'], part['name'])
    # print(name)
    scad_render_to_file(part['shape'], name,file_header=f'$fn = {SEGMENTS};')



