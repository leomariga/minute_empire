from typing import Dict, List, Optional, Any
from minute_empire.domain.village import Village
from minute_empire.repositories.village_repository import VillageRepository
from minute_empire.schemas.schemas import ResourceFieldType

class ResourceFieldService:
    """Service for resource field-related operations"""
    
    def __init__(self):
        self.village_repository = VillageRepository()
    
    
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
            # Get the production rate dictionary
            production_rates = field.get_production_rate()
            
            # Extract the production rate for this field's resource type
            field_type = field.type.value
            production_rate = production_rates.get(field_type, 0)
            
            result.append({
                "type": field_type,
                "level": field.level,
                "slot": field.slot,
                "production_rate": production_rate,
                "upgrade_cost": field.get_upgrade_cost(),
                "upgrade_time": field.get_upgrade_time(),
                "population": field.getPopulation()
            })
            
        return result
