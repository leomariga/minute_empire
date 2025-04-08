from typing import Dict, Optional, Any
from minute_empire.schemas.schemas import ResourceField, ResourceFieldType

class ResourceProducer:
    """Domain class for resource fields with production logic"""
    
    # Base costs for creating new fields
    BASE_CREATION_COSTS = {
        ResourceFieldType.FOOD: {"food": 10, "wood": 25, "stone": 25, "iron": 15},
        ResourceFieldType.WOOD: {"food": 20, "wood": 30, "stone": 40, "iron": 20},
        ResourceFieldType.STONE: {"food": 25, "wood": 40, "stone": 30, "iron": 25},
        ResourceFieldType.IRON: {"food": 30, "wood": 50, "stone": 60, "iron": 30},
    }
    
    # Base creation times in minutes
    BASE_CREATION_TIMES = {
        ResourceFieldType.FOOD: 2,
        ResourceFieldType.WOOD: 2,
        ResourceFieldType.STONE: 2,
        ResourceFieldType.IRON: 2,
    }
    
    # Base production rates per hour
    BASE_PRODUCTION_RATES = {
        ResourceFieldType.FOOD: 100,
        ResourceFieldType.WOOD: 120,
        ResourceFieldType.STONE: 100,
        ResourceFieldType.IRON: 80,
    }
    
    # Base upgrade costs
    BASE_UPGRADE_COSTS = {
        ResourceFieldType.FOOD: {"food": 20, "wood": 80, "stone": 60, "iron": 60},
        ResourceFieldType.WOOD: {"food": 60, "wood": 100, "stone": 80, "iron": 60},
        ResourceFieldType.STONE: {"food": 60, "wood": 80, "stone": 100, "iron": 60},
        ResourceFieldType.IRON: {"food": 60, "wood": 60, "stone": 80, "iron": 100},
    }
    
    # Base upgrade times in minutes
    BASE_UPGRADE_TIMES = {
        ResourceFieldType.FOOD: 1,
        ResourceFieldType.WOOD: 1,
        ResourceFieldType.STONE: 1,
        ResourceFieldType.IRON: 1,
    }
    
    @staticmethod
    def get_creation_cost(field_type: ResourceFieldType) -> Dict[str, int]:
        """
        Get the cost to create a new resource field.
        
        Args:
            field_type: Type of resource field to create
            
        Returns:
            Dict[str, int]: Resource costs for creation
        """
        if field_type not in ResourceProducer.BASE_CREATION_COSTS:
            return {}
        return ResourceProducer.BASE_CREATION_COSTS[field_type].copy()
    
    @staticmethod
    def get_creation_time(field_type: ResourceFieldType) -> int:
        """
        Get the time to create a new resource field.
        
        Args:
            field_type: Type of resource field to create
            
        Returns:
            int: Creation time in minutes
        """
        if field_type not in ResourceProducer.BASE_CREATION_TIMES:
            return 0
        return ResourceProducer.BASE_CREATION_TIMES[field_type]
    
    @staticmethod
    def can_create(field_type: ResourceFieldType, village) -> bool:
        """
        Check if a new resource field can be created.
        
        Args:
            field_type: Type of resource field to create
            village: Village where the field would be created
            
        Returns:
            bool: True if creation requirements are met
        """
        costs = ResourceProducer.get_creation_cost(field_type)
        return all(
            getattr(village.resources, resource, 0) >= amount
            for resource, amount in costs.items()
        )
    
    def __init__(self, field_data: ResourceField, village):
        self.data = field_data
        self._village = village
    
    @property
    def type(self) -> ResourceFieldType:
        """Get the resource field type"""
        return self.data.type
    
    @property
    def level(self) -> int:
        """Get the resource field level"""
        return self.data.level
    
    @property
    def slot(self) -> int:
        """Get the resource field slot"""
        return self.data.slot
    
    def get_production_rate(self, level: int = None) -> Dict[str, float]:
        """
        Get the production rate for a specific level for each resource type.
        If no level is provided, uses the current level.
        
        Args:
            level: The level to calculate the production rate for (defaults to current level)
            
        Returns:
            Dict[str, float]: Production rates per hour for each resource type
        """
        if self.type not in ResourceProducer.BASE_PRODUCTION_RATES:
            return {}
            
        base_rate = ResourceProducer.BASE_PRODUCTION_RATES[self.type]
        target_level = level if level is not None else self.level
        level_multiplier = 1.2 ** target_level  # 20% increase per level
        
        # Calculate base rate with level multiplier
        base_rate_with_level = base_rate * level_multiplier
        
        # Get building bonuses
        if hasattr(self._village, 'get_production_bonus_for_resource'):
            bonus_multiplier = 1 + self._village.get_production_bonus_for_resource(self.type.value)
            base_rate_with_level *= bonus_multiplier
        
        # Return rates for each resource type
        return {
            "wood": base_rate_with_level if self.type == ResourceFieldType.WOOD else 0,
            "stone": base_rate_with_level if self.type == ResourceFieldType.STONE else 0,
            "iron": base_rate_with_level if self.type == ResourceFieldType.IRON else 0,
            "food": base_rate_with_level if self.type == ResourceFieldType.FOOD else 0
        }
    
    def get_upgrade_cost(self) -> Dict[str, int]:
        """Calculate the cost to upgrade this resource field"""
        if self.type not in ResourceProducer.BASE_UPGRADE_COSTS:
            return {}
            
        # Apply level multiplier
        level_multiplier = 1.5 ** self.level
        return {
            resource: int(amount * level_multiplier)
            for resource, amount in ResourceProducer.BASE_UPGRADE_COSTS[self.type].items()
        }
    
    def get_upgrade_time(self) -> int:
        """Calculate upgrade time in minutes"""
        if self.type not in ResourceProducer.BASE_UPGRADE_TIMES:
            return 0
            
        # Apply level multiplier
        return int(ResourceProducer.BASE_UPGRADE_TIMES[self.type] * (1.42 ** self.level))
    
    def can_upgrade(self) -> bool:
        """Check if upgrade requirements are met"""
        costs = self.get_upgrade_cost()
        return all(
            getattr(self._village._data.resources, resource, 0) >= amount
            for resource, amount in costs.items()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert resource field to dictionary for storage or API responses"""
        return self.data.dict()
    
    def getPopulation(self) -> int:
        """
        Get the population of the resource field.
        Currently, this is simply the level of the resource field.
        
        Returns:
            int: The population of the resource field
        """
        return self.level
    
    def __str__(self) -> str:
        return f"{self.type.value} field (Level {self.level}, Slot {self.slot})" 