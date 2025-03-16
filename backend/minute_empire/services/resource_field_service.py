from typing import Dict, List, Optional, Any
from minute_empire.domain.village import Village
from minute_empire.repositories.village_repository import VillageRepository
from minute_empire.schemas.schemas import ResourceFieldType

class ResourceFieldService:
    """Service for resource field-related operations"""
    
    def __init__(self):
        self.village_repository = VillageRepository()
    
    async def upgrade_field(self, village_id: str, slot: int) -> Dict[str, Any]:
        """
        Upgrade a resource field in a village.
        
        Args:
            village_id: The ID of the village
            slot: The slot number of the field to upgrade
            
        Returns:
            Dictionary with upgrade result
        """
        village = await self.village_repository.get_by_id(village_id)
        if not village:
            return {"success": False, "error": "Village not found"}
        
        field = village.get_resource_field(slot)
        if not field:
            return {"success": False, "error": f"No resource field found in slot {slot}"}
        
        if not field.can_upgrade():
            # Get the cost to show what's missing
            costs = field.get_upgrade_cost()
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
        old_level = field.level
        field.upgrade()
        
        # Save changes
        await self.village_repository.save(village)
        
        return {
            "success": True,
            "field_type": field.type.value,
            "old_level": old_level,
            "new_level": field.level,
            "slot": field.slot
        }
    
    async def add_new_field(self, village_id: str, field_type: ResourceFieldType, 
                           slot: int) -> Dict[str, Any]:
        """
        Add a new resource field to a village.
        
        Args:
            village_id: The ID of the village
            field_type: The type of resource field to add
            slot: The slot number for the new field
            
        Returns:
            Dictionary with operation result
        """
        village = await self.village_repository.get_by_id(village_id)
        if not village:
            return {"success": False, "error": "Village not found"}
        
        # Add the field using the domain method
        if not village.add_resource_field(field_type, slot):
            return {"success": False, "error": "Failed to add resource field"}
        
        # Save changes
        await self.village_repository.save(village)
        
        return {
            "success": True,
            "field_type": field_type.value,
            "level": 1,
            "slot": slot
        }
    
    async def get_all_village_fields(self, village_id: str) -> List[Dict[str, Any]]:
        """
        Get information about all resource fields in a village.
        
        Args:
            village_id: The ID of the village
            
        Returns:
            List of dictionaries with field information
        """
        village = await self.village_repository.get_by_id(village_id)
        if not village:
            return []
        
        fields = village.get_all_resource_fields()
        
        result = []
        for field in fields:
            result.append({
                "type": field.type.value,
                "level": field.level,
                "slot": field.slot,
                "upgrade_cost": field.get_upgrade_cost(),
                "upgrade_time": field.get_upgrade_time()
            })
            
        return result
