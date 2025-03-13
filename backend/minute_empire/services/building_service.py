from typing import Dict, List, Optional, Any
from minute_empire.domain.village import Village
from minute_empire.domain.building import Building
from minute_empire.repositories.village_repository import VillageRepository
from minute_empire.schemas.schemas import ConstructionType, Construction

class BuildingService:
    """Service for building-related operations"""
    
    def __init__(self):
        self.village_repository = VillageRepository()
    
    async def upgrade_building(self, village_id: str, slot: int) -> Dict[str, Any]:
        """
        Upgrade a building in a village.
        
        Args:
            village_id: The ID of the village
            slot: The slot number of the building to upgrade
            
        Returns:
            Dictionary with upgrade result
        """
        # Get the village
        village = await self.village_repository.get_by_id(village_id)
        if not village:
            return {"success": False, "error": "Village not found"}
        
        # Get the building
        building = village.get_building(slot)
        if not building:
            return {"success": False, "error": f"No building found in slot {slot}"}
        
        # Check if we can upgrade
        if not building.can_upgrade():
            # Get the cost to show what's missing
            costs = building.get_upgrade_cost()
            resources = {
                "wood": village.resources.wood,
                "stone": village.resources.stone,
                "iron": village.resources.iron,
                "food": village.resources.food
            }
            
            missing = {}
            for resource, amount in costs.items():
                if resources.get(resource, 0) < amount:
                    missing[resource] = amount - resources.get(resource, 0)
            
            return {
                "success": False, 
                "error": "Insufficient resources",
                "cost": costs,
                "missing": missing,
                "current_resources": resources
            }
        
        # Perform the upgrade
        old_level = building.level
        building.upgrade()
        
        # Save changes
        await self.village_repository.save(village)
        
        return {
            "success": True,
            "building_type": building.type.value,
            "old_level": old_level,
            "new_level": building.level,
            "slot": building.slot
        }
    
    async def add_new_building(self, village_id: str, building_type: ConstructionType, 
                             slot: int) -> Dict[str, Any]:
        """
        Add a new building to a village.
        
        Args:
            village_id: The ID of the village
            building_type: The type of building to add
            slot: The slot number for the new building
            
        Returns:
            Dictionary with operation result
        """
        # Get the village
        village = await self.village_repository.get_by_id(village_id)
        if not village:
            return {"success": False, "error": "Village not found"}
        
        # Check if slot is already occupied
        if village.get_building(slot):
            return {"success": False, "error": f"Slot {slot} is already occupied"}
        
        # Check if we've reached the maximum number of buildings
        if len(village.get_all_buildings()) >= Village.MAX_CONSTRUCTIONS:
            return {"success": False, "error": "Maximum number of buildings reached"}
        
        # Create the new building
        new_construction = Construction(type=building_type, level=1, slot=slot)
        
        # Add it to the village constructions
        village._data.city.constructions.append(new_construction)
        
        # Mark as changed and save
        village.mark_as_changed()
        await self.village_repository.save(village)
        
        # Return success
        return {
            "success": True,
            "building_type": building_type.value,
            "level": 1,
            "slot": slot
        }
    
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
                "upgrade_time": building.get_upgrade_time()
            })
            
        return result 