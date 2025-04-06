from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from minute_empire.domain.village import Village
from minute_empire.repositories.village_repository import VillageRepository
from minute_empire.schemas.schemas import TaskType

class ResourceService:
    """Service for resource-related operations"""
    
    def __init__(self):
        self.village_repository = VillageRepository()
    
    async def update_village_resources(self, village_id: str) -> Optional[Village]:
        """
        Update a village's resources based on elapsed time since last update.
        Handles tasks that influence resource production rates by calculating
        resources in segments based on task completion times.
        
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
            # Get all completed but unprocessed construction tasks
            now = datetime.utcnow()
            last_update = village.res_update_at
            resource_affecting_tasks = []
            
            # Filter tasks that affect resource production
            if hasattr(village._data, 'construction_tasks'):
                for task in village._data.construction_tasks:
                    # We're only interested in tasks that completed after the last update
                    # but before the current update, and affect resource production
                    if (task.completion_time > last_update and 
                        task.completion_time <= now and 
                        not task.processed and
                        (task.task_type == TaskType.CREATE_FIELD or 
                         task.task_type == TaskType.UPGRADE_FIELD or 
                         task.task_type == TaskType.CREATE_BUILDING or 
                         task.task_type == TaskType.UPGRADE_BUILDING)):
                        
                        resource_affecting_tasks.append(task)
            
            # Sort tasks by completion time
            resource_affecting_tasks.sort(key=lambda t: t.completion_time)
            
            print(f"[ResourceService] Found {len(resource_affecting_tasks)} resource-affecting tasks to process")
            
            # Calculate resources in segments
            if not resource_affecting_tasks:
                # No tasks - just calculate for the whole period
                hours_elapsed = (now - last_update).total_seconds() / 3600
                print(f"[ResourceService] No resource-affecting tasks, updating for {hours_elapsed:.2f} hours")
                village.update_resources(hours_elapsed)
            else:
                # First segment: from last update to first task completion
                start_time = last_update
                
                for i, task in enumerate(resource_affecting_tasks):
                    # Calculate time segment
                    segment_hours = (task.completion_time - start_time).total_seconds() / 3600
                    print(f"[ResourceService] Updating resources for segment {i+1}: {segment_hours:.2f} hours")
                    
                    # Update resources for this segment
                    if segment_hours > 0:
                        village.update_resources(segment_hours)
                    
                    # Complete this task to update production rates
                    print(f"[ResourceService] Completing task {task.task_type} for {task.target_type} in slot {task.slot}")
                    village.complete_construction_task(task)
                    
                    # Next segment starts from this task's completion
                    start_time = task.completion_time
                
                # Final segment: from last task to now
                final_hours = (now - start_time).total_seconds() / 3600
                if final_hours > 0:
                    print(f"[ResourceService] Updating resources for final segment: {final_hours:.2f} hours")
                    village.update_resources(final_hours)
            
            # Process any remaining tasks that don't affect resources
            remaining_tasks = village.process_construction_tasks()
            if remaining_tasks:
                print(f"[ResourceService] Processed {len(remaining_tasks)} remaining tasks")
            
            # Update the resource update timestamp
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
        
        # Process any completed tasks to ensure accurate rates
        village.process_construction_tasks()
        
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