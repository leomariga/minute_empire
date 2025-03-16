from typing import Dict, Optional, Any
from minute_empire.schemas.schemas import ResourceField, ResourceFieldType

class ResourceProducer:
    """Domain class for resource fields with production logic"""
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
    
    @property
    def production_rate(self) -> float:
        """Calculate hourly production rate based on level"""
        base_rates = {
            ResourceFieldType.WOOD: 10,
            ResourceFieldType.STONE: 8,
            ResourceFieldType.IRON: 6,
            ResourceFieldType.FOOD: 12
        }
        
        if self.type not in base_rates:
            return 0
            
        # Basic formula: base_rate * (1 + 0.1 * level)
        base_production = base_rates[self.type] * (1 + 0.1 * self.level)
        
        # Apply building bonuses
        if hasattr(self._village, 'get_production_bonus_for_resource'):
            bonus_multiplier = 1 + self._village.get_production_bonus_for_resource(self.type.value)
            return base_production * bonus_multiplier
            
        return base_production
    
    def get_upgrade_cost(self) -> Dict[str, int]:
        """Calculate the cost to upgrade this resource field"""
        base_costs = {
            ResourceFieldType.WOOD: {"wood": 50, "stone": 60, "iron": 30},
            ResourceFieldType.STONE: {"wood": 60, "stone": 50, "iron": 40},
            ResourceFieldType.IRON: {"wood": 70, "stone": 80, "iron": 50},
            ResourceFieldType.FOOD: {"wood": 40, "stone": 40, "iron": 20},
        }
        
        if self.type not in base_costs:
            return {}
            
        # Apply level multiplier
        level_multiplier = 1.4 ** self.level
        return {
            resource: int(amount * level_multiplier)
            for resource, amount in base_costs[self.type].items()
        }
    
    def get_upgrade_time(self) -> int:
        """Calculate upgrade time in minutes"""
        base_times = {
            ResourceFieldType.WOOD: 10,
            ResourceFieldType.STONE: 12,
            ResourceFieldType.IRON: 15,
            ResourceFieldType.FOOD: 8,
        }
        
        if self.type not in base_times:
            return 0
            
        # Apply level multiplier
        return int(base_times[self.type] * (1.2 ** self.level))
    
    def can_upgrade(self) -> bool:
        """Check if upgrade requirements are met"""
        costs = self.get_upgrade_cost()
        return all(
            getattr(self._village._data.resources, resource, 0) >= amount
            for resource, amount in costs.items()
        )
    
    def upgrade(self) -> bool:
        """Upgrade resource field if possible"""
        if not self.can_upgrade():
            return False
            
        # Deduct resources
        upgrade_costs = self.get_upgrade_cost()
        for resource, amount in upgrade_costs.items():
            current = getattr(self._village._data.resources, resource, 0)
            setattr(self._village._data.resources, resource, current - amount)
            
        # Update field level
        self.data.level += 1
        
        # Mark village as changed
        self._village.mark_as_changed()
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert resource field to dictionary for storage or API responses"""
        return self.data.dict()
    
    def __str__(self) -> str:
        return f"{self.type.value} field (Level {self.level}, Slot {self.slot})" 