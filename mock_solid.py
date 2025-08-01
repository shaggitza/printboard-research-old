"""
Mock implementation for development without external dependencies
"""

class MockSolid:
    """Mock SolidPython functionality for development"""
    
    @staticmethod
    def cube(size, center=False):
        return MockShape("cube", {"size": size, "center": center})
    
    @staticmethod
    def cylinder(d=None, h=None, center=False):
        return MockShape("cylinder", {"d": d, "h": h, "center": center})
    
    @staticmethod
    def union():
        return MockUnion()

class MockShape:
    def __init__(self, shape_type, params):
        self.shape_type = shape_type
        self.params = params
    
    def __add__(self, other):
        return MockUnion([self, other])
    
    def __sub__(self, other):
        return MockShape("difference", {"a": self, "b": other})

class MockUnion:
    def __init__(self, shapes=None):
        self.shapes = shapes or []
    
    def __call__(self):
        return self
    
    def __add__(self, other):
        new_shapes = self.shapes + [other]
        return MockUnion(new_shapes)

# Mock functions that would normally come from solid.utils
def up(distance):
    def transform(shape):
        return MockShape("translate", {"z": distance, "shape": shape})
    return transform

def down(distance):
    def transform(shape):
        return MockShape("translate", {"z": -distance, "shape": shape})
    return transform

def left(distance):
    def transform(shape):
        return MockShape("translate", {"x": -distance, "shape": shape})
    return transform

def right(distance):
    def transform(shape):
        return MockShape("translate", {"x": distance, "shape": shape})
    return transform

def forward(distance):
    def transform(shape):
        return MockShape("translate", {"y": distance, "shape": shape})
    return transform

def back(distance):
    def transform(shape):
        return MockShape("translate", {"y": -distance, "shape": shape})
    return transform

def rotate(angles):
    def transform(shape):
        return MockShape("rotate", {"angles": angles, "shape": shape})
    return transform

def translate(vector):
    def transform(shape):
        return MockShape("translate", {"vector": vector, "shape": shape})
    return transform

def scad_render_to_file(shape, filename, file_header=""):
    """Mock SCAD file rendering"""
    print(f"Would render {shape} to {filename}")
    # Create a simple placeholder file
    with open(filename, 'w') as f:
        f.write(f"{file_header}\n// Mock SCAD output for {shape}\ncube([10,10,10]);\n")

# Mock the basic solid functions
def cube(size, center=False):
    return MockSolid.cube(size, center)

def cylinder(d=None, h=None, center=False, d1=None, **kwargs):
    params = {"d": d, "h": h, "center": center}
    if d1 is not None:
        params["d1"] = d1
    params.update(kwargs)
    return MockShape("cylinder", params)

def union():
    return MockSolid.union()

# Mock glob functionality
import glob as real_glob
def glob_glob(pattern):
    try:
        return real_glob.glob(pattern)
    except:
        return []

# Mock use function
def use(filename):
    pass

# Mock extrude functions
def extrude_along_path(shape_pts, path_pts):
    return MockShape("extrude_along_path", {"shape_pts": shape_pts, "path_pts": path_pts})

# Mock math constants
pi = 3.14159265359
tau = 2 * pi

# Make everything available at module level for import *
__all__ = [
    'MockSolid', 'MockShape', 'MockUnion',
    'up', 'down', 'left', 'right', 'forward', 'back', 'rotate', 'translate',
    'scad_render_to_file', 'cube', 'cylinder', 'union', 'use', 'extrude_along_path',
    'pi', 'tau', 'glob_glob'
]

# Set up module attributes to support from solid import *
globals().update({name: globals()[name] for name in __all__ if name in globals()})