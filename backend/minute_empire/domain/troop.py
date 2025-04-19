from datetime import timedelta
from typing import Dict, List, Tuple
from minute_empire.schemas.schemas import TroopType, Location

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
    
    # Combat statistics for each troop type
    TROOP_STATS = {
        TroopType.MILITIA: {"atk": 1, "def": 1},
        TroopType.ARCHER: {"atk": 1, "def": 0.5},
        TroopType.LIGHT_CAVALRY: {"atk": 1, "def": 1},
        TroopType.PIKEMAN: {"atk": 1, "def": 2}
    }
    
    # Backpack capacity for each troop type
    BACKPACK_CAPACITY = {
        TroopType.MILITIA: {
            "wood": 50,
            "stone": 50,
            "iron": 50,
            "food": 50,
            "total": 100  # Total capacity across all resources
        },
        TroopType.ARCHER: {
            "wood": 30,
            "stone": 30,
            "iron": 30,
            "food": 30,
            "total": 60
        },
        TroopType.LIGHT_CAVALRY: {
            "wood": 100,
            "stone": 100,
            "iron": 100,
            "food": 100,
            "total": 250  # Cavalry can carry more due to horses
        },
        TroopType.PIKEMAN: {
            "wood": 70,
            "stone": 70,
            "iron": 70,
            "food": 70,
            "total": 150
        }
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
        
    @staticmethod
    def get_valid_move_spots(troop_type: TroopType, current_location: Location) -> List[Dict[str, int]]:
        """
        Returns a list of valid locations where the troop can move based on its type
        
        Args:
            troop_type: The type of the troop
            current_location: The current location of the troop
            
        Returns:
            List of dictionaries with x, y coordinates representing valid move spots
        """
        x, y = current_location.x, current_location.y
        valid_spots = []
        
        # Adjacent cells (orthogonal)
        orthogonal = [(x, y+1), (x, y-1), (x+1, y), (x-1, y)]
        
        # Diagonal cells
        diagonal = [(x+1, y+1), (x+1, y-1), (x-1, y+1), (x-1, y-1)]
        
        # L-shaped cells (knight's move)
        l_shaped = [
            (x+2, y+1), (x+2, y-1),
            (x-2, y+1), (x-2, y-1),
            (x+1, y+2), (x-1, y+2),
            (x+1, y-2), (x-1, y-2)
        ]
        
        if troop_type == TroopType.MILITIA:
            # Militia: Adjacent cells including diagonals
            valid_coords = orthogonal + diagonal
            
        elif troop_type == TroopType.ARCHER:
            # Archer: Adjacent cells excluding diagonals
            valid_coords = orthogonal
            
        elif troop_type == TroopType.LIGHT_CAVALRY:
            # Light Cavalry: L-shaped movement like knight in chess
            valid_coords = l_shaped
            
        elif troop_type == TroopType.PIKEMAN:
            # Pikeman: Adjacent cells including diagonals + L-shaped cells
            valid_coords = orthogonal + diagonal + l_shaped
            
        # Convert to format expected by API
        for coord_x, coord_y in valid_coords:
            valid_spots.append({"x": coord_x, "y": coord_y})
            
        return valid_spots
        
    @staticmethod
    def get_valid_attack_spots(troop_type: TroopType, current_location: Location) -> List[Dict[str, int]]:
        """
        Returns a list of valid locations where the troop can attack based on its type
        
        Args:
            troop_type: The type of the troop
            current_location: The current location of the troop
            
        Returns:
            List of dictionaries with x, y coordinates representing valid attack spots
        """
        x, y = current_location.x, current_location.y
        valid_spots = []
        
        # Current cell
        current = [(x, y)]
        
        # Adjacent cells (orthogonal)
        orthogonal = [(x, y+1), (x, y-1), (x+1, y), (x-1, y)]
        
        # Diagonal cells
        diagonal = [(x+1, y+1), (x+1, y-1), (x-1, y+1), (x-1, y-1)]
        
        # L-shaped cells (knight's move)
        l_shaped = [
            (x+2, y+1), (x+2, y-1),
            (x-2, y+1), (x-2, y-1),
            (x+1, y+2), (x-1, y+2),
            (x+1, y-2), (x-1, y-2)
        ]
        
        if troop_type == TroopType.MILITIA:
            # Militia: Only current cell (must move to attack)
            valid_coords = current
            
        elif troop_type == TroopType.ARCHER:
            # Archer: Adjacent cells including diagonals
            valid_coords = orthogonal + diagonal
            
        elif troop_type == TroopType.LIGHT_CAVALRY:
            # Light Cavalry: Only current cell (must move to attack)
            valid_coords = current
            
        elif troop_type == TroopType.PIKEMAN:
            # Pikeman: L-shaped cells + current cell
            valid_coords = current + l_shaped
            
        # Convert to format expected by API
        for coord_x, coord_y in valid_coords:
            valid_spots.append({"x": coord_x, "y": coord_y})
            
        return valid_spots
        
    @staticmethod
    def get_backpack_capacity(troop_type: TroopType, quantity: int = 1) -> Dict[str, int]:
        """
        Calculate the total backpack capacity for a given troop type and quantity
        
        Args:
            troop_type: The type of the troop
            quantity: The number of troops
            
        Returns:
            Dictionary with capacity limits for each resource type and total capacity
        """
        base_capacity = Troop.BACKPACK_CAPACITY[troop_type]
        return {resource: limit * quantity for resource, limit in base_capacity.items()} 