from solid import *
from solid.utils import *
from solid.objects import *
import copy
from pprint import pprint
from euclid3 import Point2, Point3, Vector3
from math import cos, radians, sin, pi, tau
import math
import numpy as np
from math import acos
from solid.splines import bezier_polygon, bezier_points

from scipy.interpolate import CubicSpline


SHAPE_RAD = 15
SEGMENTS = 50

def create_keyboard(config):
    parts = []
    # parts.append({
    #     "name": "switch",
    #     "shape": config['switch'].switch_body
    # })
    matrix, matrix_data =  build_matrix(config, thumb_cluster=config['matrixes'].get("thumb", None))
    thumb_tubes = union()()
    if config['matrixes'].get("thumb", None):
        thumb_matrix_rotated = rotate_matrix(config, matrix_data['thumb_matrix_data'])
    merged_matrix = merge_matrix(main=matrix_data, thumb=thumb_matrix_rotated)
    tubes = build_matrix_tubes(config, merged_matrix)
    # thumb_tubes = build_matrix_tubes(config, matrix_rotated)
    parts.append({"name": "matrix", "shape": matrix+tubes+thumb_tubes})
    return parts
def merge_matrix(**args):
    new_matrix = {"pin_tube_locations": {}}
    for matrix_name in args:
        matrix = args[matrix_name]
        print(matrix, matrix_name)
        for tube in matrix["pin_tube_locations"]:
            if tube not in new_matrix["pin_tube_locations"]:
                new_matrix["pin_tube_locations"][tube] = []
            new_matrix["pin_tube_locations"][tube] += matrix["pin_tube_locations"][tube]
    print(new_matrix)
    return new_matrix
    # print(args)
def rotate_matrix(config, matrix_data):
    new_pin_tube_locations = {}
    for tube in matrix_data['pin_tube_locations']:
        for point in matrix_data['pin_tube_locations'][tube]:
            theta = math.radians(config['matrixes']['thumb'].get('rotation_angle'))
            rot_z = np.array([
                [math.cos(theta), -math.sin(theta), 0],
                [math.sin(theta), math.cos(theta), 0],
                [0, 0, 1]
            ])
            v = np.array(point).reshape((3, 1))
            v_rot = rot_z @ v
            x2, y2, z2 = v_rot.flatten()
            new_point = (x2, y2, z2)
            if tube not in new_pin_tube_locations:
                new_pin_tube_locations[tube] = []
            new_pin_tube_locations[tube].append(new_point)
    matrix_data['pin_tube_locations'] = new_pin_tube_locations
    return matrix_data

def build_matrix_tubes(config, matrix_data):
    tubes = union()()
    circle_ext = circle_points(1.7/2)
    for tube in matrix_data['pin_tube_locations'].values():
        points = []
        rounded_tube = make_round_path(tube)
        # rounded_tube = tube
        pprint([rounded_tube, tube])
        print("-"*8)
        for point in rounded_tube:
            points.append(Point3(*point))
        tubes += extrude_along_path(circle_ext, points)
    return tubes


import numpy as np
from scipy.interpolate import CubicSpline

def make_round_path(points):
    """
    Takes a list of tuple(x, y, z) objects and returns a more round path of those points
    using cubic interpolation.
    """
    # Extract x, y, z coordinates from the list of points
    x = [p[0] for p in points]
    y = [p[1] for p in points]
    z = [p[2] for p in points]

    # Calculate the cumulative distance between each pair of points
    cum_dist = [0]
    for i in range(1, len(points)):
        dx = x[i] - x[i-1]
        dy = y[i] - y[i-1]
        dz = z[i] - z[i-1]
        dist = np.sqrt(dx**2 + dy**2 + dz**2)
        cum_dist.append(cum_dist[-1] + dist)

    # Create a cubic spline interpolation of the x, y, and z coordinates
    tck_x = CubicSpline(cum_dist, x)
    tck_y = CubicSpline(cum_dist, y)
    tck_z = CubicSpline(cum_dist, z)

    # Evaluate the spline at evenly spaced intervals to get the new x, y, and z coordinates
    num_points = len(points)
    num_new_points = 10*num_points
    new_cum_dist = np.linspace(0, cum_dist[-1], num_new_points)
    new_x = tck_x(new_cum_dist)
    new_y = tck_y(new_cum_dist)
    new_z = tck_z(new_cum_dist)

    # Convert the new x, y, and z coordinates into a list of tuple(x, y, z) objects
    new_points = [(new_x[i], new_y[i], new_z[i]) for i in range(num_new_points)]
    
    return new_points
def circle_points(rad: float = SHAPE_RAD, num_points: int = SEGMENTS) -> List[Point2]:
    angles = frange(0, tau, num_steps=num_points, include_end=True)
    points = list([Point2(rad*cos(a), rad*sin(a)) for a in angles])
    return points


def build_matrix(config, matrix_keys='main', thumb_cluster=None, offset_y_thumb=0):
    matrix = union()()
    matrix_data = {
        "pin_diodes_locations":{}, 
        "pin_tube_locations":{}, 
        "switches": []
    }
    right_counter = 0 
    down_counter = 0
    last_position_x_offset = 0
    last_position_y_offset = {}
    last_points = {}
    offset_x, offset_y = config['matrixes'][matrix_keys]['offset']
    for row_elem in config['matrixes'][matrix_keys]['keys']:
        for elem in row_elem:
            if elem in config:
                move_x = last_position_x_offset + offset_x + config[elem].conf['switch_sizes_x']/2
                move_y = last_position_y_offset.get(right_counter,0)+ offset_y_thumb+ offset_y + config[elem].conf['switch_sizes_y']/2
                offset_c = 0
                if config['matrixes'][matrix_keys].get('rows_stagger'):
                    rows_stagger = config['matrixes'][matrix_keys].get('rows_stagger')
                    move_x = move_x - rows_stagger[down_counter%len(rows_stagger)]
                if config['matrixes'][matrix_keys].get('columns_stagger'):
                    columns_stagger  = config['matrixes'][matrix_keys].get('columns_stagger')
                    offset_c = columns_stagger[right_counter%len(columns_stagger)]
                    move_y = move_y - columns_stagger[right_counter%len(columns_stagger)]
                if right_counter not in matrix_data["pin_tube_locations"]:
                    matrix_data["pin_tube_locations"][right_counter] = []
                matrix_data["pin_tube_locations"][right_counter].append((  (move_x+config[elem].conf['pin_to_center_horizontal']), -(move_y -config[elem].conf['pin_clean_vertical']), - (config[elem].conf['pin_contact_height'] + config[elem].conf['switch_body_height'] + config[elem].conf['switch_body_wedge_height']) ))
                # matrix_data["pin_tube_locations"][right_counter].insert(0, (  (move_x+config[elem].conf['pin_to_center_horizontal']), offset_c, - (config[elem].conf['pin_contact_height'] + config[elem].conf['switch_body_height'] + config[elem].conf['switch_body_wedge_height']) ))
                if right_counter not in last_points:
                    last_points[right_counter] = move_x+config[elem].conf['pin_to_center_horizontal']
                matrix_data['switches'].append({
                    "column": right_counter,
                    "row": down_counter,
                    "x": move_x,
                    "y": move_y
                })
                switch_with_location = back(move_y)(
                            right(move_x )(
                                config[elem].switch_body
                            )
                        )
                last_position_x_offset += config[elem].conf['switch_sizes_x']
                if config['matrixes'][matrix_keys].get('padding_keys'):
                    paddings_list= config['matrixes'][matrix_keys]['padding_keys']
                    padding_key = paddings_list[right_counter%len(paddings_list)]
                    last_position_x_offset += padding_key
                if right_counter not in last_position_y_offset:
                    last_position_y_offset[right_counter] = 0
                last_position_y_offset[right_counter] +=  config[elem].conf['switch_sizes_y']

                matrix += switch_with_location
            else:
                print("{} does not exist ({},{})".format(elem, right_counter, down_counter))
                exit()
            right_counter += 1
        last_position_x_offset = 0
        down_counter += 1
        right_counter = 0
    # for right_counter in last_position_y_offset:
    #     matrix_data["pin_tube_locations"][right_counter].append((  last_points[right_counter], -(last_position_y_offset[right_counter]), - (config[elem].conf['pin_contact_height'] + config[elem].conf['switch_body_height'] + config[elem].conf['switch_body_wedge_height']) ))
    if config['matrixes'][matrix_keys].get('rotation_angle'):
        matrix = rotate([0, 0,config['matrixes'][matrix_keys].get('rotation_angle')])(matrix)
    if thumb_cluster:
        thumb_matrix, thumb_matrix_data = build_matrix(config, matrix_keys="thumb", offset_y_thumb=max(last_position_y_offset.values()))
        # thumb_matrix = thumb_matrix

        matrix += thumb_matrix
        matrix_data['thumb_matrix_data']  = thumb_matrix_data
        # return (thumb_matrix, thumb_cluster)
    return (matrix, matrix_data)

def empty_sw(switch, y=None, x=None, body=None):
    empty_switch = fake_sw()
    empty_switch.conf = switch.conf.copy()
    if y:
        empty_switch.conf['switch_sizes_y'] = y
    if x:
        empty_switch.conf['switch_sizes_x'] = x
    if body:
        empty_switch.switch_body = body
    return empty_switch


class fake_sw():
    conf = {}
    switch_body = union()()