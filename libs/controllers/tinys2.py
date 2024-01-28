from solid import *
from solid.utils import *
from solid.objects import *


pin_rows = {
    "left": [35, 37, 36, 14, 9, 8, 38, 33, "RST", "GND", 43, 44],
    "right": ["BAT", "GND", "5V", "3V3", 4, 5, 6, 7, 17, 18, 0]    
}

usable_pins = [35, 37, 36, 14, 9, 8, 38, 33, 43, 44, 4, 5, 6, 7, 17, 18, 0]

pin_pitch = 2.54
row_distance = 16
kmk_pin_names = {
    35: "D24",
    37: "D25",
    36: "D23",
    14: "D16",
    9:  "D11",
    8:  "D10",
    38: "D21",
    33: "D20",
    43: "D1",
    44: "D0",
    4:  "D6",
    5:  "D19",
    6:  "D18",
    7:  "D9",
    17: "D14",
    18: "D15",
    0:  "D4"
}


controller_footprint = union()()
column_ct = 0
for row in pin_rows:
    i = 0
    row_footprint = union()()
    for pin in pin_rows[row]:
        row_footprint += translate([0, pin_pitch * i, 0])(cylinder([1.5, 1.5, 1.5]))
        i += 1
    controller_footprint += translate([column_ct * row_distance, 0, 0])(row_footprint)
    column_ct += 1


# scad_render_to_file(controller_footprint, "controller_footprint.scad")    
