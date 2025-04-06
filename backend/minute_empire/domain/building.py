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
    
    # Base creation times in minutes
    BASE_CREATION_TIMES = {
        ConstructionType.CITY_CENTER: 10,
        ConstructionType.WAREHOUSE: 7,
        ConstructionType.GRANARY: 7,
        ConstructionType.WALL: 10,
        ConstructionType.RALLY_POINT: 5,
        ConstructionType.BARRAKS: 5,
        ConstructionType.ARCHERY: 10,
        ConstructionType.STABLE: 20,
        ConstructionType.HIDE_SPOT: 10,
    }

    # Defines how the resource upgrade scales with level
    CTN_TIME_LEVEL_SCALE = {
        ConstructionType.CITY_CENTER: 1.2,
        ConstructionType.WAREHOUSE: 1.2,
        ConstructionType.GRANARY: 1.24,
        ConstructionType.WALL: 1.2,
        ConstructionType.RALLY_POINT: 1.2,
        ConstructionType.BARRAKS: 1.2,
        ConstructionType.ARCHERY: 1.2,
        ConstructionType.STABLE: 1.2,
        ConstructionType.HIDE_SPOT: 1.2,
    }
    
    # Base upgrade costs
    BASE_UPGRADE_COSTS = {
        ConstructionType.CITY_CENTER: {"wood": 200, "stone": 240, "iron": 140},
        ConstructionType.WAREHOUSE: {"wood": 200, "stone": 160, "iron": 120},
        ConstructionType.GRANARY: {"wood": 180, "stone": 140, "iron": 100},
        ConstructionType.WALL: {"wood": 50, "stone": 250, "iron": 100},
        ConstructionType.RALLY_POINT: {"wood": 150, "stone": 70, "iron": 40},
        ConstructionType.BARRAKS: {"wood": 180, "stone": 150, "iron": 100},
        ConstructionType.ARCHERY: {"wood": 220, "stone": 120, "iron": 140},
        ConstructionType.STABLE: {"wood": 200, "stone": 180, "iron": 200},
        ConstructionType.HIDE_SPOT: {"wood": 100, "stone": 150, "iron": 80},
    }
    
    # Base upgrade times in minutes
    BASE_UPGRADE_TIMES = {
        ConstructionType.CITY_CENTER: 20,
        ConstructionType.WAREHOUSE: 6,
        ConstructionType.GRANARY: 4,
        ConstructionType.WALL: 10,
        ConstructionType.RALLY_POINT: 5,
        ConstructionType.BARRAKS: 10,
        ConstructionType.ARCHERY: 20,
        ConstructionType.STABLE: 30,
        ConstructionType.HIDE_SPOT: 10,
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
    def get_creation_time(building_type: ConstructionType) -> int:
        """
        Get the time to create a new building.
        
        Args:
            building_type: Type of building to create
            
        Returns:
            int: Creation time in minutes
        """
        if building_type not in Building.BASE_CREATION_TIMES:
            return 0
        return Building.BASE_CREATION_TIMES[building_type]
    
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
        if self.type not in Building.BASE_UPGRADE_COSTS:
            return {}
            
        # Apply level multiplier
        level_multiplier = 1.5 ** self.level
        return {
            resource: int(amount * level_multiplier)
            for resource, amount in Building.BASE_UPGRADE_COSTS[self.type].items()
        }
    
    def get_upgrade_time(self) -> int:
        """Calculate upgrade time in minutes"""
        if self.type not in Building.BASE_UPGRADE_TIMES:
            return 0
        if self.type not in Building.CTN_TIME_LEVEL_SCALE:
            return 0     
        # Apply level multiplier
        return int(Building.BASE_UPGRADE_TIMES[self.type] * (Building.CTN_TIME_LEVEL_SCALE[self.type] ** self.level))
    
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

    def getPopulation(self) -> int:
        """
        Get the population of the building.
        Currently, this is simply the level of the building.
        
        Returns:
            int: The population of the building
        """
        return self.level

    def __str__(self) -> str:
        return f"{self.type.value} (Level {self.level}, Slot {self.slot})" 