from datetime import datetime, timedelta
from typing import Dict, List, Optional
from minute_empire.domain.village import Village
from minute_empire.repositories.village_repository import VillageRepository

class ResourceService:
    """Service for resource-related operations"""
    
    def __init__(self):
        self.village_repository = VillageRepository()
    
    async def update_village_resources(self, village_id: str) -> Optional[Dict[str, float]]:
        """
        Update a village's resources based on elapsed time since last update.
        
        Args:
            village_id: The ID of the village
            
        Returns:
            Dict with updated resource values, or None if village not found
        """
        # Get the village
        village = await self.village_repository.get_by_id(village_id)
        if village is None:
            return None
        
        # Calculate elapsed time since last update
        now = datetime.utcnow()
        last_update = village.updated_at
        hours_elapsed = (now - last_update).total_seconds() / 3600  # Convert to hours
        
        # Get current production rates
        production_rates = village.get_resource_rates()
        
        # Update resources based on elapsed time
        village.update_resources(hours_elapsed)
        
        # Save changes to database
        await self.village_repository.save(village)
        
        # Return current resource values
        return {
            "wood": village.resources.wood,
            "stone": village.resources.stone,
            "iron": village.resources.iron,
            "food": village.resources.food,
            "production_rates": production_rates,
            "hours_elapsed": hours_elapsed
        }
    
    async def update_all_user_villages(self, user_id: str) -> List[Dict[str, float]]:
        """
        Update resources for all villages owned by a user.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            List of dictionaries with updated resource values
        """
        # Get all user villages
        villages = await self.village_repository.get_by_owner(user_id)
        if not villages:  # Return empty list if no villages
            return []
            
        results = []
        
        # Update each village
        for village in villages:
            if village is None:  # Skip if village is None
                continue
                
            try:
                # Calculate elapsed time since last update
                now = datetime.utcnow()
                last_update = village.updated_at
                hours_elapsed = (now - last_update).total_seconds() / 3600
                
                # Get current production rates
                production_rates = village.get_resource_rates()
                
                # Update resources based on elapsed time
                village.update_resources(hours_elapsed)
                
                # Save changes to database
                await self.village_repository.save(village)
                
                # Add result
                results.append({
                    "village_id": village.id,
                    "village_name": village.name,
                    "resources": {
                        "wood": village.resources.wood,
                        "stone": village.resources.stone,
                        "iron": village.resources.iron,
                        "food": village.resources.food
                    },
                    "production_rates": production_rates,
                    "hours_elapsed": hours_elapsed
                })
            except Exception as e:
                # Log error but continue with other villages
                print(f"Error updating village {village.id if village else 'unknown'}: {str(e)}")
                continue
            
        return results
    
    async def calculate_time_to_resource_goal(self, village_id: str, resource_goals: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate how long it will take to reach a resource goal.
        
        Args:
            village_id: The ID of the village
            resource_goals: Dictionary with target resource amounts
            
        Returns:
            Dictionary with hours needed for each resource
        """
        # Get the village
        village = await self.village_repository.get_by_id(village_id)
        if village is None:
            return {}
        
        # Get production rates
        rates = village.get_resource_rates()
        
        # Calculate time needed for each resource
        time_needed = {}
        for resource, goal in resource_goals.items():
            if resource not in rates or rates[resource] <= 0:
                time_needed[resource] = float('inf')  # Can't produce this resource
                continue
                
            current = getattr(village.resources, resource, 0)
            if current >= goal:
                time_needed[resource] = 0  # Already have enough
            else:
                time_needed[resource] = (goal - current) / rates[resource]
                
        return time_needed 