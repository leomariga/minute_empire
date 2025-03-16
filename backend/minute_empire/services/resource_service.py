from datetime import datetime, timedelta
from typing import Dict, List, Optional
from minute_empire.domain.village import Village
from minute_empire.repositories.village_repository import VillageRepository

class ResourceService:
    """Service for resource-related operations"""
    
    def __init__(self):
        self.village_repository = VillageRepository()
    
    async def update_village_resources(self, village_id: str) -> Optional[Village]:
        """
        Update a village's resources based on elapsed time since last update.
        
        Args:
            village_id: The ID of the village
            
        Returns:
            Updated Village object, or None if village not found
        """
        print(f"\n[ResourceService] Updating resources for village: {village_id}")
        # Get the village
        village = await self.village_repository.get_by_id(village_id)
        if village is None:
            print(f"[ResourceService] Village not found: {village_id}")
            return None
        
        try:
            # Calculate elapsed time since last update
            now = datetime.utcnow()
            last_update = village.res_update_at
            hours_elapsed = (now - last_update).total_seconds() / 3600  # Convert to hours
            
            print(f"[ResourceService] Time since last update: {hours_elapsed:.2f} hours")
            print(f"[ResourceService] Current resources: {village.resources.dict()}")
            
            # Update resources based on elapsed time
            village.update_resources(hours_elapsed)
            
            print(f"[ResourceService] Updated resources: {village.resources.dict()}")
            
            # Update res_update_at
            village.res_update_at = now
            
            # Save changes to database
            await self.village_repository.save(village)
            print(f"[ResourceService] Successfully saved updated resources for village {village_id}")
            
            return village
            
        except Exception as e:
            print(f"[ResourceService] Error updating village {village_id}: {str(e)}")
            import traceback
            print(f"[ResourceService] Error traceback:\n{traceback.format_exc()}")
            return None
    
    async def update_all_user_villages(self, user_id: str) -> List[Village]:
        """
        Update resources for all villages owned by a user.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            List of updated Village domain objects
        """
        print(f"\n[ResourceService] Updating all villages for user: {user_id}")
        # Get all user villages
        villages = await self.village_repository.get_by_owner(user_id)
        if not villages:  # Return empty list if no villages
            print(f"[ResourceService] No villages found for user {user_id}")
            return []
            
        print(f"[ResourceService] Found {len(villages)} villages for user {user_id}")
        updated_villages = []
        
        # Update each village
        for village in villages:
            if village is None:  # Skip if village is None
                continue
                
            print(f"[ResourceService] Processing village: {village.id}")
            updated_village = await self.update_village_resources(village.id)
            if updated_village:
                updated_villages.append(updated_village)
            
        print(f"[ResourceService] Successfully updated {len(updated_villages)} villages")
        return updated_villages
    
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