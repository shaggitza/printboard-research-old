
from solid import *
from solid.utils import *
import glob
SEGMENTS=50

for file_name in glob.glob("openscad-extra/src/*.scad"):
    use(file_name)

conf = {
    "side_leg_height": 1.63,
    "side_leg_width": 3.3,
    "side_leg_distance_cylinders": 1.4,
    "side_leg_width_spacer": 3,
    "mid_leg_height": 4.35,
    "mid_leg_diameter": 4,
    "mid_to_side_horizontal": 4.2,
    "pin_hole_x": 1.7,
    "pin_hole_y": 1.2,
    "pin_cone_d": 1,
    "pin_cone_d1":3, 
    "pin_cone_h": 3,
    "pin_diode_vertical":-5.2,
    "pin_clean_vertical": -5,
    "pin_to_center_horizontal":-4.7,
    "pin_contact_height": 2.6,
    "switch_body_x": 14.5,
    "switch_body_y": 14.5,
    "switch_body_height": 2,
    "switch_body_wedge_edge": 14,
    "switch_body_wedge_height": 0.7,
    "switch_sizes_x": 18.5,
    "switch_sizes_y": 18.5,
    "switch_sizes_height":8
}

pins = [
    {
        "name":"column",
        "dist_to_center": {
            "x": conf['pin_to_center_horizontal'],
            "y": -conf['pin_clean_vertical'],
            "z": conf['pin_contact_height'] + conf['switch_body_height'] + conf['switch_body_wedge_height']
        },
        "connection": "matrix"
    },
    {
        "name": "row",
        "dist_to_center": {
            "x": 0,
            "y": -conf['pin_diode_vertical'],
            "z": conf['pin_contact_height'] + conf['switch_body_height'] + conf['switch_body_wedge_height']

        },
        "connection": "matrix"
    }
]

pin_coords = [conf['pin_to_center_horizontal'], conf['pin_clean_vertical']]
pin_diode_coords  = [0, conf['pin_diode_vertical']]

leg_side =  cube([conf['side_leg_width'], conf['side_leg_width_spacer'], conf['side_leg_height']], center=True)
leg_side += forward(-conf['side_leg_distance_cylinders'])(cylinder(d=conf['side_leg_width'], h=conf['side_leg_height'], center=True))
leg_side += forward(conf['side_leg_distance_cylinders'])(cylinder(d=conf['side_leg_width'], h=conf['side_leg_height'],center=True))

leg_center = cylinder(d=conf['mid_leg_diameter'], h=conf['mid_leg_height'], center=True)

switch_footprint =   up(conf['side_leg_height']/2)(left(-conf['mid_to_side_horizontal'])(leg_side))
switch_footprint +=  up(conf['mid_leg_height']/2)(leg_center)
switch_footprint +=  up(conf['side_leg_height']/2)(left(conf['mid_to_side_horizontal'])(leg_side))


pin_hole =  up(conf['mid_leg_height']/2)(cube([conf['pin_hole_x'],conf['pin_hole_y'],conf['mid_leg_height']], center=True))
pin_hole +=  cylinder(d=conf['pin_cone_d'], d1=conf['pin_cone_d1'], h=conf['pin_cone_h'])

switch_pin_holes =  back(conf['pin_clean_vertical'])(right(conf['pin_to_center_horizontal'])(rotate([0, 0, 90])(pin_hole))) + back(conf['pin_diode_vertical'])(pin_hole)

switch_body_lock =   down(conf['switch_body_height']/2) (cube([conf['switch_body_x'], conf['switch_body_y'], conf['switch_body_height']], center=True)) 
switch_body_lock +=  down(conf['switch_body_height'] + conf['switch_body_wedge_height']/2)(cube([conf['switch_body_wedge_edge'], conf['switch_body_wedge_edge'], conf['switch_body_wedge_height']], center=True))

switch_body = rotate([0, 180, 180])(up(conf['switch_body_wedge_height']  +conf['switch_body_height'] )(switch_footprint+switch_pin_holes+switch_body_lock))


# switch_body_real = up(conf['switch_sizes_height']/2)(cube([conf['switch_sizes_x'], conf['switch_sizes_y'], conf['switch_sizes_height']], center=True)) - switch_body
# scad_render_to_file(switch_body_real, 'switch_footprint.scad',file_header=f'$fn = {SEGMENTS};') 