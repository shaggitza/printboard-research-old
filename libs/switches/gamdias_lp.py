
from math import cos, sin
from solid import *
from solid.utils import *
import glob
SEGMENTS=50


def quarter_torus(outer_radius, tube_radius, angle=90):
    # Define the path (a quarter circle)
    path = []
    segments = SEGMENTS
    for i in range(segments + 1):
        theta = (angle * pi / 180) * i / segments
        x = outer_radius * cos(theta)
        y = outer_radius * sin(theta)
        path.append([x, y, 0])

    

    # Define the shape to be extruded (a circle)
    shape = []
    for i in range(segments + 1):
        theta = (2 * pi) * i / segments
        x = tube_radius * cos(theta)
        y = tube_radius * sin(theta)
        shape.append([x, y])

    # Extrude the shape along the path
    return extrude_along_path(shape_pts=shape, path_pts=path)


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
    "switch_sizes_height":8,
    # "diode_slot_x"
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
            "x": 5,
            "y": 8,
            "z": 3 + conf['pin_contact_height'] + conf['switch_body_height'] + conf['switch_body_wedge_height']+0.6
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


arc_diode_hole = quarter_torus(conf['mid_leg_height']/2, 1.7/2)
arc_diode_end = cylinder(d=1.7, h=1.5, center=True)
arc_diode_end = rotate([90, 0, 0])(arc_diode_end)
arc_diode_end = back(0.7)(arc_diode_end)
arc_diode_end = right(2.17)(arc_diode_end)
diode_body_hole = cube([8, 4, 4], center=True)
diode_clearance = cube([16, 2, 4], center=True)
diode_second_leg_hole = cube([10, 2, 2], center=True)
diode_second_leg_hole = back(1)(left(5)(down(3)(diode_second_leg_hole)))

diode_slot = arc_diode_hole + arc_diode_end + forward(1.5)(left(4)(diode_body_hole)) +  forward(-1)(left(0)(diode_clearance)) + diode_second_leg_hole

diode_slot = rotate([-90, 180, 0])(diode_slot)
diode_slot = forward(conf['pin_diode_vertical'])(diode_slot)
diode_slot = right(2)(diode_slot)
diode_slot = down(5)(diode_slot)
diode_slot = down(3)(diode_slot)





# scad_render_to_file(diode_slot, 'diode_slot.scad',file_header=f'$fn = {SEGMENTS};')





switch_body = rotate([0, 180, 180])(up(conf['switch_body_wedge_height']  +conf['switch_body_height'] )(switch_footprint+switch_pin_holes+switch_body_lock))
# switch_body = rotate([0, 180, 180])(up(conf['switch_body_wedge_height']  +conf['switch_body_height'] )(switch_footprint+switch_pin_holes+switch_body_lock)) + diode_slot

# switch_body += diode_slot
# switch_body = down(conf['switch_sizes_height']/2)(cube([conf['switch_sizes_x'], conf['switch_sizes_y'], conf['switch_sizes_height']], center=True)) - switch_body
# switch_body = cube([conf['switch_sizes_x'], conf['switch_sizes_y'], conf['switch_sizes_height']], center=True) - switch_body
# scad_render_to_file(switch_body, 'switch_footprint.scad',file_header=f'$fn = {SEGMENTS};') 
