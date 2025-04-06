from typing import Dict, List, Optional, Any
from minute_empire.domain.village import Village
from minute_empire.domain.building import Building
from minute_empire.repositories.village_repository import VillageRepository
from minute_empire.schemas.schemas import ConstructionType, Construction

class BuildingService:
    """Service for building-related operations"""
    
    def __init__(self):
        self.village_repository = VillageRepository()
    
    async def get_all_village_buildings(self, village_id: str) -> List[Dict[str, Any]]:
        """
        Get information about all buildings in a village.
        
        Args:
            village_id: The ID of the village
            
        Returns:
            List of dictionaries with building information
        """
        # Get the village
        village = await self.village_repository.get_by_id(village_id)
        if not village:
            return []
        
        # Get all buildings
        buildings = village.get_all_buildings()
        
        # Create result list
        result = []
        for building in buildings:
            result.append({
                "type": building.type.value,
                "level": building.level,
                "slot": building.slot,
                "upgrade_cost": building.get_upgrade_cost(),
                "upgrade_time": building.get_upgrade_time(),
                "population": building.getPopulation()
            })
            
        return result 