from solid import *
from solid.utils import *
import copy
from pprint import pprint
from euclid3 import Point2, Point3, Vector3
from math import cos, radians, sin, pi, tau

SHAPE_RAD = 15
SEGMENTS = 50

def create_keyboard(config):
    parts = []
    # parts.append({
    #     "name": "switch",
    #     "shape": config['switch'].switch_body
    # })
    matrix, matrix_data =  build_matrix(config, thumb_cluster=config['matrixes'].get("thumb", None))
    pprint(matrix_data)
    tubes = build_matrix_tubes(config, matrix_data)
    parts.append({"name": "matrix", "shape": matrix+tubes})
    return parts
def build_matrix_tubes(config, matrix_data):
    tubes = union()()
    circle_ext = circle_points(1.7/2)
    for tube in matrix_data['pin_tube_locations'].values():
        points = []
        for point in tube:
            points.append(Point3(*point))
        tubes += extrude_along_path(circle_ext, points)
    return tubes

def circle_points(rad: float = SHAPE_RAD, num_points: int = SEGMENTS) -> List[Point2]:
    angles = frange(0, tau, num_steps=num_points, include_end=True)
    points = list([Point2(rad*cos(a), rad*sin(a)) for a in angles])
    return points

def build_matrix(config, matrix_keys='main', thumb_cluster=None):
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
                move_y = last_position_y_offset.get(right_counter,0)+ offset_y + config[elem].conf['switch_sizes_y']/2
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
                matrix_data["pin_tube_locations"][right_counter].insert(0, (  (move_x+config[elem].conf['pin_to_center_horizontal']), offset_c, - (config[elem].conf['pin_contact_height'] + config[elem].conf['switch_body_height'] + config[elem].conf['switch_body_wedge_height']) ))
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
    for right_counter in last_position_y_offset:
        matrix_data["pin_tube_locations"][right_counter].append((  last_points[right_counter], -(last_position_y_offset[right_counter]), - (config[elem].conf['pin_contact_height'] + config[elem].conf['switch_body_height'] + config[elem].conf['switch_body_wedge_height']) ))
    if config['matrixes'][matrix_keys].get('rotation_angle'):
        matrix = rotate([0, 0,config['matrixes'][matrix_keys].get('rotation_angle')])(matrix)
    if thumb_cluster:
        thumb_matrix, thumb_matrix_data = build_matrix(config, matrix_keys="thumb")
        thumb_matrix = back(max(last_position_y_offset.values()))(thumb_matrix)

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