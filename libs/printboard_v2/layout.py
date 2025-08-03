"""
Layout planning for V2 API

Handles the mathematical planning of key positions, staggering, rotation, etc.
Separated from 3D modeling concerns.
"""

import math
from typing import List, Tuple, Dict, Any
from dataclasses import dataclass

from .config import KeyboardConfig, MatrixConfig
from .switches import SwitchInterface


@dataclass
class KeyPosition:
    """Represents a planned key position."""
    row: int
    col: int
    x: float
    y: float
    z: float = 0.0
    angle: float = 0.0
    matrix_name: str = "main"
    
    @property
    def label(self) -> str:
        """Human readable key label."""
        return f"R{self.row}C{self.col}"


@dataclass  
class LayoutPlan:
    """Complete layout plan for a keyboard."""
    keys: List[KeyPosition]
    matrices: Dict[str, Tuple[float, float]]  # matrix_name -> (width, height)
    total_bounds: Tuple[float, float, float, float]  # min_x, min_y, max_x, max_y
    
    def get_keys_for_matrix(self, matrix_name: str) -> List[KeyPosition]:
        """Get all keys belonging to a specific matrix."""
        return [key for key in self.keys if key.matrix_name == matrix_name]


class LayoutPlanner:
    """Plans keyboard layouts with proper positioning and spacing."""
    
    def __init__(self, switch: SwitchInterface):
        self.switch = switch
        self.key_size = switch.specs.key_size[0]  # Assume square keys
    
    def plan_layout(self, config: KeyboardConfig) -> LayoutPlan:
        """Plan complete keyboard layout from configuration."""
        all_keys = []
        matrices = {}
        
        for matrix_name, matrix_config in config.matrices.items():
            keys = self._plan_matrix(matrix_config, matrix_name)
            all_keys.extend(keys)
            
            # Calculate matrix bounds
            if keys:
                min_x = min(key.x for key in keys)
                max_x = max(key.x for key in keys)
                min_y = min(key.y for key in keys)
                max_y = max(key.y for key in keys)
                matrices[matrix_name] = (max_x - min_x + self.key_size, 
                                       max_y - min_y + self.key_size)
        
        # Calculate total bounds
        if all_keys:
            min_x = min(key.x for key in all_keys)
            max_x = max(key.x for key in all_keys)
            min_y = min(key.y for key in all_keys)
            max_y = max(key.y for key in all_keys)
            total_bounds = (min_x, min_y, max_x, max_y)
        else:
            total_bounds = (0, 0, 0, 0)
        
        return LayoutPlan(
            keys=all_keys,
            matrices=matrices,
            total_bounds=total_bounds
        )
    
    def _plan_matrix(self, matrix_config: MatrixConfig, matrix_name: str) -> List[KeyPosition]:
        """Plan positions for a single matrix."""
        keys = []
        
        for row in range(matrix_config.rows):
            for col in range(matrix_config.cols):
                position = self._calculate_key_position(
                    row, col, matrix_config, matrix_name
                )
                keys.append(position)
        
        return keys
    
    def _calculate_key_position(self, row: int, col: int, 
                              matrix_config: MatrixConfig, 
                              matrix_name: str) -> KeyPosition:
        """Calculate position for a single key."""
        # Base position
        x = col * self.key_size
        y = row * self.key_size
        z = 0.0
        key_angle = 0.0
        
        # Apply row staggering
        if matrix_config.rows_stagger and row < len(matrix_config.rows_stagger):
            x -= matrix_config.rows_stagger[row]
        
        # Apply column staggering
        if matrix_config.columns_stagger and col < len(matrix_config.columns_stagger):
            y -= matrix_config.columns_stagger[col]
        
        # Calculate individual key angle
        if matrix_config.rows_angle and row < len(matrix_config.rows_angle):
            key_angle += matrix_config.rows_angle[row]
        if matrix_config.columns_angle and col < len(matrix_config.columns_angle):
            key_angle += matrix_config.columns_angle[col]
        
        # Apply matrix rotation
        if matrix_config.rotation_angle != 0:
            angle_rad = math.radians(matrix_config.rotation_angle)
            cos_a = math.cos(angle_rad)
            sin_a = math.sin(angle_rad)
            new_x = x * cos_a - y * sin_a
            new_y = x * sin_a + y * cos_a
            x, y = new_x, new_y
        
        # Apply matrix offset
        x += matrix_config.offset[0]
        y += matrix_config.offset[1]
        
        return KeyPosition(
            row=row,
            col=col,
            x=x,
            y=y,
            z=z,
            angle=key_angle,
            matrix_name=matrix_name
        )
    
    def generate_preview_data(self, config: KeyboardConfig) -> List[List[Dict[str, Any]]]:
        """Generate 2D preview data compatible with existing UI."""
        layout_plan = self.plan_layout(config)
        
        # Group keys by matrix and organize by row/col for UI
        preview_data = []
        
        # For now, just handle the main matrix for backward compatibility
        main_keys = layout_plan.get_keys_for_matrix("main")
        if not main_keys:
            return []
        
        # Organize keys into row/column structure
        max_row = max(key.row for key in main_keys)
        max_col = max(key.col for key in main_keys)
        
        for row in range(max_row + 1):
            row_data = []
            for col in range(max_col + 1):
                # Find key at this row/col
                key = next((k for k in main_keys if k.row == row and k.col == col), None)
                if key:
                    key_data = {
                        'x': key.x,
                        'y': key.y,
                        'width': self.key_size,
                        'height': self.key_size,
                        'angle': key.angle,
                        'label': key.label
                    }
                    row_data.append(key_data)
            if row_data:  # Only add non-empty rows
                preview_data.append(row_data)
        
        return preview_data