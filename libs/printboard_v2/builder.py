"""
Keyboard builder for V2 API

Main builder class that orchestrates keyboard construction using clean separation of concerns.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import datetime
import uuid

from .config import KeyboardConfig, MatrixConfig
from .switches import SwitchInterface, switch_registry
from .controllers import ControllerInterface, controller_registry
from .layout import LayoutPlanner, LayoutPlan
from .modeling import ModelingEngine


@dataclass
class KeyboardPart:
    """Represents a generated keyboard part."""
    name: str
    shape: Any  # 3D geometry object
    part_type: str  # "matrix", "controller", "case", etc.


@dataclass
class KeyboardResult:
    """Complete keyboard generation result."""
    config: KeyboardConfig
    layout_plan: LayoutPlan
    parts: List[KeyboardPart]
    metadata: Dict[str, Any]


class KeyboardBuilder:
    """Main builder class for constructing keyboards with V2 API."""
    
    def __init__(self):
        self.switch_registry = switch_registry
        self.controller_registry = controller_registry
        self.modeling_engine = ModelingEngine()
    
    def _generate_unique_name(self, base_name: str = "keyboard") -> str:
        """Generate a unique keyboard name with timestamp."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        short_uuid = str(uuid.uuid4())[:8]
        return f"{base_name}_{timestamp}_{short_uuid}"
    
    def create_simple_keyboard(self, 
                             name: str,
                             rows: int, 
                             cols: int,
                             switch_type: str = "gamdias_lp",
                             controller_type: str = "tinys2") -> KeyboardResult:
        """Create a simple keyboard with basic grid layout."""
        
        # Generate unique name
        unique_name = self._generate_unique_name(name)
        
        # Create configuration
        matrix_config = MatrixConfig(rows=rows, cols=cols)
        config = KeyboardConfig(
            name=unique_name,
            switch_type=switch_type,
            controller_type=controller_type,
            matrices={"main": matrix_config}
        )
        
        return self.build_keyboard(config)
    
    def build_keyboard(self, config: KeyboardConfig) -> KeyboardResult:
        """Build complete keyboard from configuration."""
        
        # Get components
        switch = self.switch_registry.get(config.switch_type)
        controller = self.controller_registry.get(config.controller_type)
        
        # Plan layout
        planner = LayoutPlanner(switch)
        layout_plan = planner.plan_layout(config)
        
        # Generate 3D parts
        parts = self._generate_parts(config, layout_plan, switch, controller)
        
        # Collect metadata
        metadata = {
            "switch_type": config.switch_type,
            "controller_type": config.controller_type,
            "total_keys": len(layout_plan.keys),
            "matrices": list(config.matrices.keys()),
            "bounds": layout_plan.total_bounds
        }
        
        return KeyboardResult(
            config=config,
            layout_plan=layout_plan,
            parts=parts,
            metadata=metadata
        )
    
    def _generate_parts(self, 
                       config: KeyboardConfig,
                       layout_plan: LayoutPlan,
                       switch: SwitchInterface,
                       controller: ControllerInterface) -> List[KeyboardPart]:
        """Generate 3D parts for the keyboard using new modeling engine."""
        
        # Use the new modeling engine instead of legacy code
        parts_data = self.modeling_engine.create_keyboard_parts(config)
        
        # Convert to V2 format
        v2_parts = []
        for part in parts_data:
            v2_parts.append(KeyboardPart(
                name=part['name'],
                shape=part['shape'],
                part_type="matrix"  # Currently only supporting matrix parts
            ))
        
        return v2_parts
    
    def generate_preview(self, config: KeyboardConfig) -> List[List[Dict[str, Any]]]:
        """Generate 2D preview data for the UI."""
        switch = self.switch_registry.get(config.switch_type)
        planner = LayoutPlanner(switch)
        return planner.generate_preview_data(config)
    
    def create_config_from_web_request(self, request_data: Dict[str, Any]) -> KeyboardConfig:
        """Create configuration from web API request data."""
        
        # Extract basic parameters
        base_name = request_data.get('name', 'custom_keyboard')
        unique_name = self._generate_unique_name(base_name)
        rows = request_data.get('rows', 5)
        cols = request_data.get('cols', 5)
        switch_type = request_data.get('switchType', 'gamdias_lp')
        controller_type = request_data.get('controllerType', 'tinys2')
        
        # Controller placement
        controller_lr = request_data.get('controllerPlacementLR', 'left')
        controller_tb = request_data.get('controllerPlacementTB', 'top')
        
        # Matrix configuration
        matrix_config = MatrixConfig(
            rows=rows,
            cols=cols,
            offset=(
                request_data.get('matrixOffsetX', 0),
                request_data.get('matrixOffsetY', 0)
            ),
            rows_stagger=request_data.get('rowsStagger'),
            columns_stagger=request_data.get('columnsStagger'),
            rows_angle=request_data.get('rowsAngle'),
            columns_angle=request_data.get('columnsAngle'),
            rotation_angle=request_data.get('rotationAngle', 0),
            padding_keys=request_data.get('paddingKeys')
        )
        
        # Create keyboard configuration
        config = KeyboardConfig(
            name=unique_name,
            switch_type=switch_type,
            controller_type=controller_type,
            controller_placement=(controller_lr, controller_tb),
            matrices={"main": matrix_config}
        )
        
        return config
    
    def list_available_switches(self) -> List[str]:
        """List available switch types."""
        return self.switch_registry.list_switches()
    
    def list_available_controllers(self) -> List[str]:
        """List available controller types."""
        return self.controller_registry.list_controllers()


# Global builder instance for easy access
keyboard_builder = KeyboardBuilder()