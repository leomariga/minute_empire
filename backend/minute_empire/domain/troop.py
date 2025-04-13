from datetime import timedelta
from typing import Dict
from minute_empire.schemas.schemas import TroopType

class Troop:
    """Domain class for troops with game logic"""
    
    TRAINING_COSTS = {
        TroopType.MILITIA: {"wood": 50, "stone": 30, "iron": 20, "food": 10},
        TroopType.ARCHER: {"wood": 70, "stone": 40, "iron": 30, "food": 20},
        TroopType.LIGHT_CAVALRY: {"wood": 100, "stone": 60, "iron": 50, "food": 30},
        TroopType.PIKEMAN: {"wood": 80, "stone": 50, "iron": 40, "food": 25}
    }
    
    TRAINING_TIMES = {
        TroopType.MILITIA: 1,  # in minutes
        TroopType.ARCHER: 1,
        TroopType.LIGHT_CAVALRY: 1,
        TroopType.PIKEMAN: 1
    }
    
    @staticmethod
    def get_training_cost(troop_type: TroopType, quantity: int) -> Dict[str, int]:
        """Calculate the total training cost for a given troop type and quantity"""
        base_cost = Troop.TRAINING_COSTS[troop_type]
        return {resource: cost * quantity for resource, cost in base_cost.items()}
    
    @staticmethod
    def get_training_time(troop_type: TroopType, quantity: int) -> int:
        """Calculate the total training time for a given troop type and quantity"""
        base_time = Troop.TRAINING_TIMES[troop_type]
        return base_time * quantity 