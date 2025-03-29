from typing import Dict, Optional, Any
from minute_empire.schemas.schemas import ConstructionType, Construction

class Building:
    """Domain class for buildings with game logic"""
    
    # Base costs for creating new buildings
    BASE_CREATION_COSTS = {
        ConstructionType.CITY_CENTER: {"wood": 150, "stone": 180, "iron": 100},
        ConstructionType.WAREHOUSE: {"wood": 70, "stone": 90, "iron": 50},
        ConstructionType.GRANARY: {"wood": 60, "stone": 75, "iron": 40},
        ConstructionType.WALL: {"wood": 30, "stone": 200, "iron": 80},
        ConstructionType.RALLY_POINT: {"wood": 100, "stone": 50, "iron": 30},
        ConstructionType.BARRAKS: {"wood": 130, "stone": 120, "iron": 80},
        ConstructionType.ARCHERY: {"wood": 170, "stone": 100, "iron": 100},
        ConstructionType.STABLE: {"wood": 150, "stone": 150, "iron": 150},
        ConstructionType.HIDE_SPOT: {"wood": 70, "stone": 120, "iron": 60},
    }
    
    # Base production bonuses for buildings
    BASE_PRODUCTION_BONUSES = {
        ConstructionType.CITY_CENTER: 0.05,  # 5% bonus per level
        ConstructionType.WAREHOUSE: 0.03,    # 3% bonus per level
        ConstructionType.GRANARY: 0.03,      # 3% bonus per level
        ConstructionType.WALL: 0.02,         # 2% bonus per level
        ConstructionType.RALLY_POINT: 0.0,   # No production bonus
        ConstructionType.BARRAKS: 0.0,       # No production bonus
        ConstructionType.ARCHERY: 0.0,       # No production bonus
        ConstructionType.STABLE: 0.0,        # No production bonus
        ConstructionType.HIDE_SPOT: 0.0,     # No production bonus
    }
    
    @staticmethod
    def get_creation_cost(building_type: ConstructionType) -> Dict[str, int]:
        """
        Get the cost to create a new building.
        
        Args:
            building_type: Type of building to create
            
        Returns:
            Dict[str, int]: Resource costs for creation
        """
        if building_type not in Building.BASE_CREATION_COSTS:
            return {}
        return Building.BASE_CREATION_COSTS[building_type].copy()
    
    @staticmethod
    def can_create(building_type: ConstructionType, village) -> bool:
        """
        Check if a new building can be created.
        
        Args:
            building_type: Type of building to create
            village: Village where the building would be created
            
        Returns:
            bool: True if creation requirements are met
        """
        costs = Building.get_creation_cost(building_type)
        return all(
            getattr(village.resources, resource, 0) >= amount
            for resource, amount in costs.items()
        )
    
    def __init__(self, construction: Construction, village):
        self.data = construction
        self._village = village
        
    @property
    def type(self) -> ConstructionType:
        return self.data.type
        
    @property
    def level(self) -> int:
        return self.data.level
        
    @property
    def slot(self) -> int:
        return self.data.slot
    
    def get_upgrade_cost(self) -> Dict[str, int]:
        """Calculate upgrade cost based on building type and level"""
        base_costs = {
            ConstructionType.CITY_CENTER: {"wood": 200, "stone": 240, "iron": 140},
            ConstructionType.WAREHOUSE: {"wood": 100, "stone": 120, "iron": 70},
            ConstructionType.GRANARY: {"wood": 80, "stone": 100, "iron": 60},
            ConstructionType.WALL: {"wood": 50, "stone": 250, "iron": 100},
            ConstructionType.RALLY_POINT: {"wood": 150, "stone": 70, "iron": 40},
            ConstructionType.BARRAKS: {"wood": 180, "stone": 150, "iron": 100},
            ConstructionType.ARCHERY: {"wood": 220, "stone": 120, "iron": 140},
            ConstructionType.STABLE: {"wood": 200, "stone": 180, "iron": 200},
            ConstructionType.HIDE_SPOT: {"wood": 100, "stone": 150, "iron": 80},
        }
        
        if self.type not in base_costs:
            return {}
            
        # Apply level multiplier
        level_multiplier = 1.5 ** self.level
        return {
            resource: int(amount * level_multiplier)
            for resource, amount in base_costs[self.type].items()
        }
    
    def get_upgrade_time(self) -> int:
        """Calculate upgrade time in minutes"""
        base_times = {
            ConstructionType.CITY_CENTER: 30,
            ConstructionType.WAREHOUSE: 20,
            ConstructionType.GRANARY: 20,
            ConstructionType.WALL: 15,
            ConstructionType.RALLY_POINT: 10,
            ConstructionType.BARRAKS: 25,
            ConstructionType.ARCHERY: 25,
            ConstructionType.STABLE: 30,
            ConstructionType.HIDE_SPOT: 15,
        }
        
        if self.type not in base_times:
            return 0
            
        # Apply level multiplier
        return int(base_times[self.type] * (1.2 ** self.level))
    
    def can_upgrade(self) -> bool:
        """Check if upgrade requirements are met"""
        costs = self.get_upgrade_cost()
        return all(
            getattr(self._village.resources, resource, 0) >= amount
            for resource, amount in costs.items()
        )
    
    def get_production_bonus(self, level: int = None) -> Dict[str, float]:
        """
        Get the production bonus for a specific level for each resource type.
        If no level is provided, uses the current level.
        
        Args:
            level: The level to calculate the bonus for (defaults to current level)
            
        Returns:
            Dict[str, float]: Production bonuses as multipliers for each resource type
        """
        if self.type not in Building.BASE_PRODUCTION_BONUSES:
            return {}
            
        base_bonus = Building.BASE_PRODUCTION_BONUSES[self.type]
        target_level = level if level is not None else self.level
        bonus_value = base_bonus * target_level
        
        # Return bonuses for each resource type
        return {
            "wood": bonus_value,
            "stone": bonus_value,
            "iron": bonus_value,
            "food": bonus_value
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert building to dictionary for storage or API responses"""
        return self.data.dict()

    def __str__(self) -> str:
        return f"{self.type.value} (Level {self.level}, Slot {self.slot})" 