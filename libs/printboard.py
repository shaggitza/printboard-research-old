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
    build = union()()
    matrixes  = {}
    offset_v = 0
    for matrix_name in config['matrixes']:
        matrixes[matrix_name] =  plan_matrix(config, matrix_name=matrix_name)
        matrixes[matrix_name] = fix_rotation_matrix_data(matrixes[matrix_name], config)
        build += draw_matrix(matrixes[matrix_name], config)
        pprint(matrixes[matrix_name])
        size_x, size_y = matrixes[matrix_name]['sizes']
        offset_v += size_y
    parts.append({"name": "matrix", "shape": build})
    return parts
def draw_matrix(matrix_data, config):
    ret = union()()
    for switch in matrix_data['switches']:
        ret += back(switch['y'])(
                right(switch['x'])(
                    rotate([0, 0, switch['c_angle']])(
                        switch['switch'].switch_body
                    )
                )
            )
    return ret
def fix_rotation_matrix_data(matrix_data, config):
    max_x= max_y = 0
    matrix_config = matrix_data['matrix_config']
    real_matrix = {}
    for switch in matrix_data['switches']:
        if switch['row'] not in real_matrix:
            real_matrix[switch['row']] = {}
        real_matrix[switch['row']][switch['column']] = switch
    for switch in matrix_data['switches']:
        offset_y = offset_x = 0
        if switch['c_angle'] != 0:
            lowest_row = max(real_matrix.keys())
            lowest_switch = real_matrix[lowest_row] [switch['column']]
            vertical_leg = (lowest_switch['y'] -  switch['y'])
            if vertical_leg != 0:
                angle_radians = math.radians(-int(switch['c_angle']))
                offset_x = -vertical_leg * math.sin(angle_radians)
        switch['y'] += offset_y
        switch['x'] += offset_x
        switch['c_angle'] = -switch['c_angle']
        max_x = max(max_x, switch['x'])
        max_y = max(max_y, switch['y'])
    matrix_data['sizes'] = (max_x, max_y)
    return matrix_data
def merge_matrix(**args):
    new_matrix = {"pin_tube_locations": {}}
    for matrix_name in args:
        matrix = args[matrix_name]
        print(matrix, matrix_name)
        for tube in matrix["pin_tube_locations"]:
            if tube not in new_matrix["pin_tube_locations"]:
                new_matrix["pin_tube_locations"][tube] = []
            new_matrix["pin_tube_locations"][tube] += matrix["pin_tube_locations"][tube]
    return new_matrix
def rotate_point(point, angle):
    theta = angle
    rot_z = np.array([
        [math.cos(theta), -math.sin(theta), 0],
        [math.sin(theta), math.cos(theta), 0],
        [0, 0, 1]
    ])
    v = np.array(point).reshape((3, 1))
    v_rot = rot_z @ v
    x2, y2, z2 = v_rot.flatten()
    new_point = (x2, y2, z2)
    return new_point
# def build_matrix_tubes(config, matrix_data):
#     tubes = union()()
#     circle_ext = circle_points(1.7/2)
#     for tube in matrix_data['pin_tube_locations'].values():
#         points = []
#         rounded_tube = make_round_path(tube)
#         # rounded_tube = tube
#         pprint([rounded_tube, tube])
#         print("-"*8)
#         for point in rounded_tube:
#             points.append(Point3(*point))
#         tubes += extrude_along_path(circle_ext, points)
#     return tubes


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



def plan_matrix(config, matrix_name='main', thumb_cluster=None, offset_y_thumb=0):
    # Initialize matrix data dictionary
    matrix_data = {
        "pin_diodes_locations": {},
        "pin_tube_locations": {},
        "switches": []
    }
    
    # Initialize counters and offsets
    matrix_config =  config['matrixes'][matrix_name]
    matrix_data['matrix_config'] = matrix_config
    right_counter = 0 
    down_counter = 0
    last_position_x_offset = 0
    last_position_y_offset = {}
    last_points = {}
    offset_x, offset_y = matrix_config['offset']
    max_y = max_x = 0
    # Loop through each element in the matrix
    for row in matrix_config['keys']:
        for element in row:
            # If the element exists in the configuration file
            if element in config:
                # Calculate the x and y position of the switch
                move_x = last_position_x_offset + offset_x + config[element].conf['switch_sizes_x'] / 2
                move_y = last_position_y_offset.get(right_counter, 0) + offset_y_thumb + offset_y + config[element].conf['switch_sizes_y'] / 2
                c_angle = 0
                r_angle = 0
                if matrix_config.get('columns_angle', False):
                    c_angle = matrix_config.get('columns_angle', [])[right_counter % len(matrix_config['columns_angle'])]
                if matrix_config.get('rows_angle', False):
                    r_angle = matrix_config.get('rows_angle', [])[down_counter % len(matrix_config['rows_angle'])]
                # Apply row and column staggering if specified
                if 'rows_stagger' in matrix_config:
                    stagger = matrix_config.get('rows_stagger', [])[down_counter % len(matrix_config['rows_stagger'])]
                    move_x -= stagger
                if 'columns_stagger' in matrix_config:
                    stagger = matrix_config.get('columns_stagger', [])[right_counter % len(matrix_config['columns_stagger'])]
                    move_y -= stagger
                
                # Add the switch to the matrix data dictionary
                matrix_data['switches'].append({
                    "switch": config[element],
                    "column": right_counter,
                    "row": down_counter,
                    "x": move_x,
                    "y": move_y,
                    "c_angle": c_angle,
                    "r_angle": r_angle
                })
                max_x = max(max_x, move_x)
                max_y = max(max_y, move_y)
                # Update the position offsets for the next element
                last_position_x_offset += config[element].conf['switch_sizes_x']
                if 'padding_keys' in matrix_config:
                    padding = matrix_config['padding_keys'][right_counter % len(matrix_config['padding_keys'])]
                    last_position_x_offset += padding
                if right_counter not in last_position_y_offset:
                    last_position_y_offset[right_counter] = 0
                last_position_y_offset[right_counter] += config[element].conf['switch_sizes_y']
            else:
                # If the element does not exist in the configuration file, raise an exception
                raise Exception(f"{element} does not exist ({right_counter},{down_counter})")
            
            # Increment counters
            right_counter += 1
        last_position_x_offset = 0
        down_counter += 1
        right_counter = 0
    matrix_data['sizes'] = (max_x, max_y)
    # Return the matrix data dictionary
    return matrix_data


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

def circle_points(rad: float = SHAPE_RAD, num_points: int = SEGMENTS) -> List[Point2]:
    angles = frange(0, tau, num_steps=num_points, include_end=True)
    points = list([Point2(rad*cos(a), rad*sin(a)) for a in angles])
    return points