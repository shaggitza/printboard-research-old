"""
Configuration objects for V2 API

Immutable configuration classes that define keyboard specifications.
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
import copy


@dataclass(frozen=True)
class MatrixConfig:
    """Configuration for a single switch matrix."""
    
    rows: int
    cols: int
    offset: Tuple[float, float] = (0.0, 0.0)
    rows_stagger: Optional[List[float]] = None
    columns_stagger: Optional[List[float]] = None
    rows_angle: Optional[List[float]] = None
    columns_angle: Optional[List[float]] = None
    rotation_angle: float = 0.0
    padding_keys: Optional[List[float]] = None
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.rows <= 0 or self.cols <= 0:
            raise ValueError("Rows and columns must be positive integers")
        
        # Validate stagger/angle lists if provided
        if self.rows_stagger and len(self.rows_stagger) != self.rows:
            raise ValueError(f"rows_stagger must have {self.rows} elements")
        if self.columns_stagger and len(self.columns_stagger) != self.cols:
            raise ValueError(f"columns_stagger must have {self.cols} elements")
        if self.rows_angle and len(self.rows_angle) != self.rows:
            raise ValueError(f"rows_angle must have {self.rows} elements")
        if self.columns_angle and len(self.columns_angle) != self.cols:
            raise ValueError(f"columns_angle must have {self.cols} elements")


@dataclass(frozen=True)
class KeyboardConfig:
    """Complete keyboard configuration."""
    
    name: str
    switch_type: str = "gamdias_lp"
    controller_type: str = "tinys2"
    controller_placement: Tuple[str, str] = ("left", "top")
    matrices: Dict[str, MatrixConfig] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.name:
            raise ValueError("Keyboard name cannot be empty")
        
        if not self.matrices:
            raise ValueError("At least one matrix must be defined")
        
        # Validate controller placement
        lr, tb = self.controller_placement
        if lr not in ("left", "right"):
            raise ValueError("Controller LR placement must be 'left' or 'right'")
        if tb not in ("top", "bottom"):
            raise ValueError("Controller TB placement must be 'top' or 'bottom'")
    
    def with_matrix(self, name: str, matrix: MatrixConfig) -> 'KeyboardConfig':
        """Return a new config with an added matrix."""
        new_matrices = dict(self.matrices)
        new_matrices[name] = matrix
        return KeyboardConfig(
            name=self.name,
            switch_type=self.switch_type,
            controller_type=self.controller_type,
            controller_placement=self.controller_placement,
            matrices=new_matrices
        )
    
    def with_name(self, name: str) -> 'KeyboardConfig':
        """Return a new config with updated name."""
        return KeyboardConfig(
            name=name,
            switch_type=self.switch_type,
            controller_type=self.controller_type,
            controller_placement=self.controller_placement,
            matrices=self.matrices
        )
    
    def to_legacy_format(self) -> Dict[str, Any]:
        """Convert to legacy printboard format for backward compatibility."""
        # Import here to avoid circular dependency
        from ..switches import gamdias_lp as switch
        from ..controllers import tinys2 as controller
        from .. import printboard as kb
        
        legacy_matrices = {}
        for matrix_name, matrix_config in self.matrices.items():
            # Create basic matrix
            keys = [["switch"] * matrix_config.cols for _ in range(matrix_config.rows)]
            
            matrix_dict = {
                "offset": matrix_config.offset,
                "keys": keys
            }
            
            # Add optional parameters
            if matrix_config.rows_angle:
                matrix_dict["rows_angle"] = list(matrix_config.rows_angle)
            if matrix_config.columns_angle:
                matrix_dict["columns_angle"] = list(matrix_config.columns_angle)
            if matrix_config.rows_stagger:
                matrix_dict["rows_stagger"] = list(matrix_config.rows_stagger)
            if matrix_config.columns_stagger:
                matrix_dict["columns_stagger"] = list(matrix_config.columns_stagger)
            if matrix_config.rotation_angle != 0:
                matrix_dict["rotation_angle"] = matrix_config.rotation_angle
            if matrix_config.padding_keys:
                matrix_dict["padding_keys"] = list(matrix_config.padding_keys)
            
            legacy_matrices[matrix_name] = matrix_dict
        
        layout = {
            "name": self.name,
            "controller_placement": self.controller_placement,
            "matrixes": legacy_matrices,
            "switch": switch,
            "empty_switch": kb.empty_sw(switch),
            "controller": controller
        }
        
        # Add variable key sizes
        for i in range(0, 7):
            for num in [0, 0.25, 0.5, 0.75]:
                total_i = i + num
                if int(total_i) == total_i:
                    total_i = int(total_i)
                layout[f"{total_i}u"] = kb.empty_sw(switch, body=switch.switch_body, pins=switch.pins, x=18.5*total_i)
        
        return layout