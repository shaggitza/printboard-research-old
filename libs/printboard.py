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
import random
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
        # pprint(matrixes[matrix_name])
        # exit()
        # pprint(matrixes[matrix_name])
        build += draw_matrix(matrixes[matrix_name], config)
        size_x, size_y = matrixes[matrix_name]['sizes']
        offset_v += size_y
    #this should generate the paths to the controller pins, as per the data in the controller class, this should not do the controller jack plug
    # - generate list of points of contact with all switches pins
    # - arrange pins in a matrix based on their position, nearest pin for query so tha tthe matrix looks at least sane if not fully working
    # - should return only points for the tubes, not other type of data, no 3d modelling here, just 2d stuff and some fake contact points to keep the tube to not hit into the other stuff  
    # 
    tubes = plan_tubes(config, matrixes)
    # tubes = amplify_tubes_curves(tubes)
    tubes = draw_tubes(tubes, config)
    tubes = rotate([180, 0, 0])(tubes)
    # controller_shield = make_controller_points(config, controller_contacts) 
    build += tubes
    # build = union()()

    # best_pins_list = controller_pins(config)
    # controller = draw_controller(config, controller_config)

    # exit()
    
    # build = cube([1000, 1000, 1000]) - build
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
def draw_tubes(tubes, config):
    ret = union()()
    for tube in tubes:
        ret += build_matrix_tubes(config, tube)
    return ret

def plan_tubes(config, matrixes):
    points = extract_points(matrixes)
    runs = 100
    traces = {
        "rows": [],
        "columns": []
    }
    while   runs > 0:
        rows, columns = arrange_points_in_matrix(points['matrix'])
        traces['rows'].append(rows)
        traces['columns'].append(columns)
        runs -= 1
        

    
    rows = best_traces(traces['rows'])
    columns = best_traces(traces['columns'])

    rows = rows[0]
    columns = columns[0]
    # rows_new = []
    #getting all columns  to the starting edge (up)
    columns_new = []
    for column in columns:
        starting_point = column[-1]
        _x, _y, _z  = starting_point
        column.append((_x, 0, _z))
        columns_new.append(column)
    columns = columns_new
    # same for rows (untested)
    rows_new = []
    for row in rows:
        starting_point = row[-1]
        _x, _y, _z  = starting_point
        row.append((0, _y, _z))
        rows_new.append(row)
    rows = rows_new
    # points = round_points(points)
    # rows, columns = arrange_points_in_matrix_old(points['matrix'])
    rounded_points = []
    for column_points in columns:
        # column_points = make_round_path(column_points)
        rounded_points.append(column_points)
    for row_points in rows:
        # row_points = make_round_path(row_points)
        rounded_points.append(row_points)
    return rounded_points

from shapely.geometry import LineString

def controller_pins(config):
    controller_info  = config['controller']
    placement_lr, placement_tb = config['controller_placement']
    usable_pins = config['controller'].usable_pins
    pins_list = []
    
    closest_row = controller_info.pin_rows["left" if placement_lr == "right" else "right"]
    farthest_row = controller_info.pin_rows["right" if placement_lr == "right" else "left"]

    # usable_pins
    closest_usable_pins = [pin for pin in closest_row if pin in usable_pins]
    farthest_usable_pins = [pin for pin in farthest_row if pin in usable_pins]


    pprint(["closest_row", closest_usable_pins])
    pprint(["farthest_row", farthest_usable_pins])

    controller_footprint 
    


def check_intersection(line1, line2):
    """Check if two line segments intersect."""
    l1 = LineString(line1)
    l2 = LineString(line2)
    return l1.intersects(l2)

def best_traces(traces):
    traces = traces
    scores = []
    for trace in traces:
        scores.append(compute_scores_for_iteration_updated(trace[0], trace[1]))
    best_score = 0
    best_score_index = 0
    best_score_traces_count = 0
    for i in range(0, len(scores)):
        score = sum(scores[i])
        traces_count = len(scores[i])
        weight = score/traces_count if traces_count > 0 else 0
        if weight > best_score:
            best_score = weight
            best_score_index = i
            best_score_traces_count = traces_count
        elif weight == best_score:
            if traces_count < best_score_traces_count:
                best_score = weight
                best_score_index = i
                best_score_traces_count = traces_count
    return traces[best_score_index]

def compute_y_score_updated(y):
    """Compute the score based on the y-coordinate of the start point."""
    if y == 0:
        return 1
    elif y <= 5:
        return 0.75
    elif y <= 10:
        return 0.5
    elif y <= 15:
        return 0.25
    else:
        return 0

def compute_scores_for_iteration_updated(columns, unconnected):
    """Compute scores for an iteration's columns."""
    scores = []
    
    for col in columns:
        # Determine the start point based on Y-coordinate
        if col[0][1] < col[-1][1]:
            start_point_y = col[0][1]
        else:
            start_point_y = col[-1][1]
        
        # Start Point Y Score
        y_score = compute_y_score_updated(start_point_y)
        
        # Intersection Score
        intersection_score = 1
        for other_col in columns:
            if col != other_col and check_intersection(col, other_col):
                intersection_score = 0
                break
                
        # Total score for the column
        total_score = y_score * intersection_score
        scores.append(total_score)

    # if unconnected > 0:
    for i in range(0, unconnected):
        scores.append(0)
    return scores

def arrange_points_in_matrix(points_list):
    def arrange_by_distance(points, key_filter, unconnected_points=None):
        if unconnected_points is None:
            unconnected_points = []
        next_point = {}
        location_map = {}
        for point in points:
            location_map[point['location']] = point
            if point['location'] in next_point:
                continue
            point_x, point_y, point_z = point['location']
            points_map = {}
            for other_point in points:
                if other_point['location'] in next_point.values():
                    continue
                other_point_x, other_point_y, other_point_z = other_point['location']
                if key_filter(point, other_point):
                    distance = ((other_point_x - point_x) ** 2 + (other_point_y - point_y) ** 2) ** 0.5
                    if distance not in points_map:
                        points_map[distance] = []
                    points_map[distance].append(other_point)
            if len(points_map) > 0:
                sorted_points_map = sorted(points_map.keys())
                best_distance = None
                if len(sorted_points_map) > 1:
                    distance_between_first_two = sorted_points_map[0] - sorted_points_map[1]
                    if abs(distance_between_first_two) < sorted_points_map[0]*0.2:
                        best_distance = random.choice(sorted_points_map[0:2])
                    else:
                        best_distance = min(sorted_points_map)
                if not best_distance:
                    best_distance = min(points_map.keys())
                if best_distance > (other_point['switch'].conf['switch_sizes_y']*2):
                    unconnected_points.append(point)
                else:
                    chosen_point = points_map[best_distance][0]
                    next_point[point['location']] = chosen_point['location']
            else:
                unconnected_points.append(point)
        return next_point

    rows = [point for point in points_list if point['name'] in ['row', 'rows']]
    columns = [point for point in points_list if point['name'] in ['column', 'columns']]

    column_filter = lambda point, other_point: other_point['row'] < point['row']
    row_filter = lambda point, other_point: other_point['row'] == point['row'] and other_point != point

    unconnected_points = []
    next_column_point = arrange_by_distance(columns, column_filter, unconnected_points)
    next_row_point = arrange_by_distance(rows, row_filter, unconnected_points)

    # Connect unconnected points
    # connected_points = set()
    # for unconnected_point in unconnected_points:
    #     if unconnected_point['location'] not in connected_points:
    #         connected_points.add(unconnected_point['location'])
    #         if unconnected_point['name'] in ['row', 'rows']:
    #             next_row_point.update(arrange_by_distance([unconnected_point], row_filter))
    #         elif unconnected_point['name'] in ['column', 'columns']:
    #             next_column_point.update(arrange_by_distance([unconnected_point], column_filter))

    def build_paths(next_point):
        start_points = set(next_point.keys()) - set(next_point.values())
        # pprint(["start_points", start_points])
        paths = []
        for start_point in start_points:
            path = []
            while start_point:
                path.append(start_point)
                start_point = next_point.get(start_point, False)
            paths.append(path)
        return paths

    real_matrix_columns = build_paths(next_column_point)
    real_matrix_rows = build_paths(next_row_point)
    real_unconnected_points = set([unconnected_point['location'] for unconnected_point in unconnected_points]) - set(list(next_row_point.keys())) - set(list(next_column_point.keys())) - set(list(next_row_point.values())) - set(list(next_column_point.values()))
    real_unconnected_points_rows = [point for point in real_unconnected_points if point in [point['location'] for point in rows]]
    real_unconnected_points_columns = [point for point in real_unconnected_points if point in [point['location'] for point in columns]]


        
    # Debug output removed to reduce noise
    # pprint(["real_unconnected_points_rows", real_unconnected_points_rows])
    # pprint(["real_unconnected_points_columns", real_unconnected_points_columns])

    return [real_matrix_rows, len(real_unconnected_points_rows)], [real_matrix_columns, len(real_unconnected_points_columns)]



def extract_points(matrixes):
    return_arr = {}
    for matrix_name in matrixes:
        for switch in matrixes[matrix_name]['switches']:
            for pin in switch['switch'].pins:
                if pin['connection'] not in return_arr:
                    return_arr[pin['connection']] = []
                point_x, point_y, point_z = rotate_point((pin['dist_to_center']['x'], pin['dist_to_center']['y'], pin['dist_to_center']['z']), switch['c_angle'])
                point_x += switch['x']
                point_y += switch['y']
                # print(switch['column'], switch['row'])
                point_obj = {
                    "name": pin['name'],
                    "column": switch['column'],
                    "row": switch['row'],
                    "switch": switch['switch'],
                    "location": (point_x, point_y, point_z),
                }

                return_arr[pin['connection']].append(point_obj)

    return return_arr
    

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
            lowest_switch = real_matrix[lowest_row]
            if switch['column'] in lowest_switch:
                lowest_switch = lowest_switch[switch['column']]
                vertical_leg = (lowest_switch['y'] -  switch['y'])
            else:
                vertical_leg = 0
            if vertical_leg != 0:
                angle_radians = math.radians(-int(switch['c_angle']))
                offset_x = -vertical_leg * math.sin(angle_radians)
        switch['y'] += offset_y
        switch['x'] += offset_x
        switch['c_angle'] = -switch['c_angle']
        max_x = max(max_x, switch['x'])
        max_y = max(max_y, switch['y'])
        new_pins =  []
        for pin_data in switch['switch'].pins:
            if switch['c_angle'] != 0 : 
                pin_x, pin_y, pin_z =  (pin_data['dist_to_center']['x'], pin_data['dist_to_center']['y'], pin_data['dist_to_center']['z'])
                point = rotate_point((pin_x, pin_y, pin_z), switch['c_angle'])
                new_pin_x, new_pin_y, new_pin_z = point
                pin_data['dist_to_center']['x'] = new_pin_x
                pin_data['dist_to_center']['y'] = new_pin_y
                pin_data['dist_to_center']['z'] = new_pin_z
                # print(-switch['c_angle'], (pin_x, pin_y, pin_z), (new_pin_x, new_pin_y, new_pin_z))
            new_pins.append(pin_data)
        switch['switch'].pins = new_pins
    matrix_data['sizes'] = (max_x, max_y)
    return matrix_data
def merge_matrix(**args):
    new_matrix = {"pin_tube_locations": {}}
    for matrix_name in args:
        matrix = args[matrix_name]
        # print(matrix, matrix_name)
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
def build_matrix_tubes(config, rounded_tube):
    circle_ext = circle_points(1.7/2)
    points = []
    for point in rounded_tube:
        points.append(Point3(*point))
    return extrude_along_path(circle_ext, points)
    # return tubes


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


def empty_sw(switch, y=None, x=None, body=None, pins=None):
    empty_switch = fake_sw()
    empty_switch.conf = switch.conf.copy()
    if y:
        empty_switch.conf['switch_sizes_y'] = y
    if x:
        empty_switch.conf['switch_sizes_x'] = x
    if body:
        empty_switch.switch_body = body
    if pins:
        empty_switch.pins = pins
    return empty_switch


class fake_sw():
    conf = {}
    pins = {}
    switch_body = union()()

def circle_points(rad: float = SHAPE_RAD, num_points: int = SEGMENTS) -> List[Point2]:
    angles = frange(0, tau, num_steps=num_points, include_end=True)
    points = list([Point2(rad*cos(a), rad*sin(a)) for a in angles])
    return points