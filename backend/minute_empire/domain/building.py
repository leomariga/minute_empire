from typing import Dict, Optional
from minute_empire.schemas.schemas import ConstructionType, Construction

class Building:
    """Domain class for buildings with game logic"""
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
    
    def upgrade(self) -> bool:
        """Upgrade building if possible"""
        if not self.can_upgrade():
            return False
            
        # Deduct resources
        upgrade_costs = self.get_upgrade_cost()
        for resource, amount in upgrade_costs.items():
            current = getattr(self._village._data.resources, resource, 0)
            setattr(self._village._data.resources, resource, current - amount)
            
        # Update building level
        self.data.level += 1
        
        # Mark village as changed
        self._village.mark_as_changed()
        return True
    
    def get_production_bonus(self, resource_type: str) -> float:
        """Get production bonus for a specific resource"""
        # Example: City center provides small bonus to all resources
        if self.type == ConstructionType.CITY_CENTER:
            return 0.05 * self.level  # 5% bonus per level
            
        # Specialized buildings could provide larger bonuses to specific resources
        return 0.0
    
    def __str__(self) -> str:
        return f"{self.type.value} (Level {self.level}, Slot {self.slot})" 