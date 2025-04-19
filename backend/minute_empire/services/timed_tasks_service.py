from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from minute_empire.repositories.village_repository import VillageRepository
from minute_empire.schemas.schemas import TaskType, ConstructionTask 
from minute_empire.schemas.schemas import ConstructionType, ResourceFieldType, TroopType
from minute_empire.services.building_service import BuildingService
from minute_empire.services.resource_field_service import ResourceFieldService
from minute_empire.domain.resource_field import ResourceProducer
from minute_empire.domain.building import Building
from minute_empire.domain.troop import Troop
from bson import ObjectId
from minute_empire.repositories.troops_repository import TroopsRepository
from minute_empire.repositories.troop_action_repository import TroopActionRepository
from minute_empire.services.task_scheduler import task_scheduler
from minute_empire.services.troop_action_service import TroopActionService
from minute_empire.services.websocket_service import websocket_service
import logging
import asyncio
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskCategory(str, Enum):
    """Enum to identify the category of task for sorting purposes"""
    CONSTRUCTION = "construction"
    TROOP_TRAINING = "troop_training"
    TROOP_ACTION = "troop_action"

@dataclass
class TaskData:
    """Data class to hold task information for sorting"""
    task_id: str
    village_id: str  # May be empty for troop actions
    completion_time: datetime
    category: TaskCategory
    data: Any  # Original task object

class TimedConstructionService:
    """
    Service for managing timed construction of buildings and fields.
    Acts as a coordinator between domain objects and existing services.
    """
    
    def __init__(self):
        self.village_repository = VillageRepository()
        self.building_service = BuildingService()
        self.resource_field_service = ResourceFieldService()
        self.troops_repository = TroopsRepository()
        self.troop_action_repository = TroopActionRepository()
        self.troop_action_service = None  # Initialize on first use to avoid circular imports

    def _get_troop_action_service(self):
        """Lazy initialization of troop action service to avoid circular imports"""
        if self.troop_action_service is None:
            from minute_empire.services.troop_action_service import TroopActionService
            self.troop_action_service = TroopActionService()
        return self.troop_action_service

    async def get_pending_tasks(self, village_id: str) -> List[Dict[str, Any]]:
        """
        Get all pending construction tasks for a village.
        
        Args:
            village_id: The ID of the village
            
        Returns:
            List[Dict[str, Any]]: Pending construction tasks
        """
        # Get the village
        village = await self.village_repository.get_by_id(village_id)
        if not village:
            return []
            
        # Get pending tasks
        now = datetime.utcnow()
        pending_tasks = []
        
        if hasattr(village._data, 'construction_tasks'):
            for task in village._data.construction_tasks:
                if not task.processed:
                    pending_tasks.append({
                        "id": task.id,
                        "task_type": task.task_type,
                        "target_type": task.target_type,
                        "slot": task.slot,
                        "level": task.level,
                        "started_at": task.started_at,
                        "completion_time": task.completion_time,
                        "time_remaining_seconds": max(0, (task.completion_time - now).total_seconds())
                    })
            
        return pending_tasks
    
    async def start_building_construction(self, village_id: str, building_type: ConstructionType, 
                                       slot: int) -> Dict[str, Any]:
        """
        Start timed building construction instead of creating it immediately.
        
        Args:
            village_id: The ID of the village
            building_type: Type of building to create
            slot: Slot number for the building
            
        Returns:
            Dict[str, Any]: Result of the operation
        """
        # Validate the building creation first
        validation_result = await self._validate_building_creation(village_id, building_type, slot)
        if not validation_result["success"]:
            return validation_result
            
        # Get the village after validation
        village = await self.village_repository.get_by_id(village_id)
        
        # Deduct resources for the task
        from minute_empire.domain.building import Building
        costs = Building.get_creation_cost(building_type)
        if not village.deduct_resources(costs):
            return {
                "success": False,
                "error": "Insufficient resources",
                "cost": costs
            }
            
        # Get the creation time in minutes
        duration = Building.get_creation_time(building_type) if hasattr(Building, 'get_creation_time') else 30
        
        # Create task
        task = village.add_construction_task(
            TaskType.CREATE_BUILDING,
            building_type.value,
            slot,
            duration
        )
        
        # Save changes
        await self.village_repository.save(village)
        
        # Schedule the task completion
        await task_scheduler.schedule_task(
            task_id=task.id,
            execution_time=task.completion_time,
            callback=self.complete_construction_task,
            village_id=village_id,
            task_id_param=task.id,
            completion_time=task.completion_time
        )
        
        return {
            "success": True,
            "building_type": building_type.value,
            "slot": slot,
            "estimated_completion": task.completion_time,
            "task_id": task.id
        }
        
    async def start_field_construction(self, village_id: str, field_type: ResourceFieldType, 
                                    slot: int) -> Dict[str, Any]:
        """
        Start timed resource field construction instead of creating it immediately.
        
        Args:
            village_id: The ID of the village
            field_type: Type of field to create
            slot: Slot number for the field
            
        Returns:
            Dict[str, Any]: Result of the operation
        """
        # Validate the field creation first
        validation_result = await self._validate_field_creation(village_id, field_type, slot)
        if not validation_result["success"]:
            return validation_result
            
        # Get the village after validation
        village = await self.village_repository.get_by_id(village_id)
        
        # Deduct resources for the task
        from minute_empire.domain.resource_field import ResourceProducer
        costs = ResourceProducer.get_creation_cost(field_type)
        if not village.deduct_resources(costs):
            return {
                "success": False,
                "error": "Insufficient resources",
                "cost": costs
            }
            
        # Get creation time in minutes
        duration = ResourceProducer.get_creation_time(field_type) if hasattr(ResourceProducer, 'get_creation_time') else 20
        
        # Create task
        task = village.add_construction_task(
            TaskType.CREATE_FIELD,
            field_type.value,
            slot,
            duration
        )
        
        # Save changes
        await self.village_repository.save(village)
        
        # Schedule the task completion
        await task_scheduler.schedule_task(
            task_id=task.id,
            execution_time=task.completion_time,
            callback=self.complete_construction_task,
            village_id=village_id,
            task_id_param=task.id,
            completion_time=task.completion_time
        )
        
        return {
            "success": True,
            "field_type": field_type.value,
            "slot": slot,
            "estimated_completion": task.completion_time,
            "task_id": task.id
        }
        
    async def start_building_upgrade(self, village_id: str, slot: int) -> Dict[str, Any]:
        """
        Start timed building upgrade instead of upgrading it immediately.
        
        Args:
            village_id: The ID of the village
            slot: Slot of the building to upgrade
            
        Returns:
            Dict[str, Any]: Result of the operation
        """
        # Validate upgrade first
        validation_result = await self._validate_building_upgrade(village_id, slot)
        if not validation_result["success"]:
            return validation_result
            
        # Get the village and building after validation
        village = await self.village_repository.get_by_id(village_id)
        building = village.get_building(slot)
        
        # Deduct resources for the task
        costs = building.get_upgrade_cost()
        if not village.deduct_resources(costs):
            return {
                "success": False,
                "error": "Insufficient resources",
                "cost": costs
            }
            
        # Get the upgrade time in minutes
        duration = building.get_upgrade_time()
        
        # Create task
        task = village.add_construction_task(
            TaskType.UPGRADE_BUILDING,
            building.type.value,
            slot,
            duration
        )
        
        # Set target level
        task.level = building.level + 1
        
        # Save changes
        await self.village_repository.save(village)
        
        # Schedule the task completion
        await task_scheduler.schedule_task(
            task_id=task.id,
            execution_time=task.completion_time,
            callback=self.complete_construction_task,
            village_id=village_id,
            task_id_param=task.id,
            completion_time=task.completion_time
        )
        
        return {
            "success": True,
            "building_type": building.type.value,
            "old_level": building.level,
            "new_level": building.level + 1,
            "slot": slot,
            "estimated_completion": task.completion_time,
            "task_id": task.id
        }
        
    async def start_field_upgrade(self, village_id: str, slot: int) -> Dict[str, Any]:
        """
        Start timed field upgrade instead of upgrading it immediately.
        
        Args:
            village_id: The ID of the village
            slot: Slot of the field to upgrade
            
        Returns:
            Dict[str, Any]: Result of the operation
        """
        # Validate upgrade first
        validation_result = await self._validate_field_upgrade(village_id, slot)
        if not validation_result["success"]:
            return validation_result
            
        # Get the village and field after validation
        village = await self.village_repository.get_by_id(village_id)
        field = village.get_resource_field(slot)
        
        # Deduct resources for the task
        costs = field.get_upgrade_cost()
        if not village.deduct_resources(costs):
            return {
                "success": False,
                "error": "Insufficient resources",
                "cost": costs
            }
            
        # Get the upgrade time in minutes
        duration = field.get_upgrade_time()
        
        # Create task
        task = village.add_construction_task(
            TaskType.UPGRADE_FIELD,
            field.type.value,
            slot,
            duration
        )
        
        # Set target level
        task.level = field.level + 1
        
        # Save changes
        await self.village_repository.save(village)
        
        # Schedule the task completion
        await task_scheduler.schedule_task(
            task_id=task.id,
            execution_time=task.completion_time,
            callback=self.complete_construction_task,
            village_id=village_id,
            task_id_param=task.id,
            completion_time=task.completion_time
        )
        
        return {
            "success": True,
            "field_type": field.type.value,
            "old_level": field.level,
            "new_level": field.level + 1,
            "slot": slot,
            "estimated_completion": task.completion_time,
            "task_id": task.id
        }
        
    async def start_troop_training(self, village_id: str, troop_type: TroopType, quantity: int) -> Dict[str, Any]:
        """
        Start timed troop training.
        
        Args:
            village_id: The ID of the village
            troop_type: Type of troop to train
            quantity: Number of troops to train
            
        Returns:
            Dict[str, Any]: Result of the operation
        """
        # Validate the troop training first
        validation_result = await self._validate_troop_training(village_id, troop_type, quantity)
        if not validation_result["success"]:
            return validation_result
            
        # Get the village after validation
        village = await self.village_repository.get_by_id(village_id)
        
        # Deduct resources for the task
        costs = Troop.get_training_cost(troop_type, quantity)
        if not village.deduct_resources(costs):
            return {
                "success": False,
                "error": "Insufficient resources",
                "cost": costs
            }
            
        # Get the training time in minutes
        duration = Troop.get_training_time(troop_type, quantity)
        
        # Create task
        task = village.add_troop_training_task(
            troop_type.value,
            quantity,
            duration
        )
        
        # Save changes
        await self.village_repository.save(village)
        
        # Schedule the task completion
        await task_scheduler.schedule_task(
            task_id=task.id,
            execution_time=task.completion_time,
            callback=self.complete_troop_training_task,
            village_id=village_id,
            task_id_param=task.id,
            completion_time=task.completion_time
        )
        
        return {
            "success": True,
            "troop_type": troop_type.value,
            "quantity": quantity,
            "estimated_completion": task.completion_time,
            "task_id": task.id
        }
    
    async def update_resources_until(self, village_id: str, target_time: datetime) -> Optional[Any]:
        """
        Update village resources up to a specific point in time.
        This is used before task completion to ensure resources are calculated with correct rates.
        
        Args:
            village_id: The ID of the village
            target_time: The time to update resources until
            
        Returns:
            Optional[Any]: Updated village or None if not found
        """
        # Get the village
        village = await self.village_repository.get_by_id(village_id)
        if not village:
            logger.error(f"Village {village_id} not found for resource update")
            return None
            
        # Calculate how much time has passed since the last update
        last_update = village.res_update_at
        hours_elapsed = (target_time - last_update).total_seconds() / 3600
        
        if hours_elapsed <= 0:
            logger.info(f"No time elapsed for village {village_id}, skipping update")
            return village
            
        logger.info(f"Updating resources for village {village_id} for {hours_elapsed:.2f} hours until {target_time}")
        
        # Update resources
        village.update_resources(hours_elapsed)
        
        # Update the resource update timestamp to the target time
        village.res_update_at = target_time
        
        # Save changes
        await self.village_repository.save(village)
        return village
    
    async def complete_construction_task(self, village_id: str, task_id_param: str, completion_time: datetime) -> Dict[str, Any]:
        """
        Complete a construction task. This is called by the task scheduler.
        
        Args:
            village_id: The ID of the village
            task_id_param: The ID of the task that's being completed
            completion_time: The scheduled completion time of the task
            
        Returns:
            Dict[str, Any]: Result of the operation
        """
        try:
            # First update resources with the correct rates up to the completion time
            village = await self.update_resources_until(village_id, completion_time)
            if not village:
                return {"success": False, "error": "Village not found"}
            
            # Find the task to complete
            task = None
            if hasattr(village._data, 'construction_tasks'):
                task = next((t for t in village._data.construction_tasks if t.id == task_id_param), None)
            
            if not task:
                return {"success": False, "error": "Task not found"}
            
            # Complete the task
            village.complete_construction_task(task)
            
            # Save changes
            await self.village_repository.save(village)
            
            logger.info(f"Completed construction task {task_id_param} for village {village_id}")
            
            # Broadcast map update to the village owner via WebSocket
            await websocket_service.broadcast_construction_complete(village_id)
            
            return {
                "success": True,
                "task_id": task_id_param,
                "task_type": task.task_type,
                "completion_time": completion_time
            }
        except Exception as e:
            logger.error(f"Error completing construction task {task_id_param}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {"success": False, "error": str(e)}
        
    async def complete_troop_training_task(self, village_id: str, task_id_param: str, completion_time: datetime) -> Dict[str, Any]:
        """
        Complete a troop training task by creating the trained troops.
        
        Args:
            village_id: The ID of the village
            task_id_param: The ID of the task that's being completed
            completion_time: The scheduled completion time of the task
            
        Returns:
            Dict[str, Any]: Result of the operation
        """
        try:
            # First update resources with the correct rates up to the completion time
            village = await self.update_resources_until(village_id, completion_time)
            if not village:
                return {"success": False, "error": "Village not found"}
            
            # Find the task to get its details
            task = None
            if hasattr(village._data, 'troop_training_tasks'):
                task = next((t for t in village._data.troop_training_tasks if t.id == task_id_param), None)
            
            if not task:
                return {"success": False, "error": "Task not found"}
            
            # Mark the task as processed
            task.processed = True
            village.mark_as_changed()
            
            # Create the troop data
            troop_data = {
                "_id": str(ObjectId()),
                "type": task.troop_type,
                "quantity": task.quantity,
                "home_id": village_id,
                "location": village.location,
                "mode": "idle",
                "backpack": {
                    "wood": 0,
                    "stone": 0,
                    "iron": 0,
                    "food": 0
                },
                "created_at": completion_time,  # Use completion time, not current time
                "updated_at": completion_time   # Use completion time, not current time
            }
            
            # Save the village with the processed task
            await self.village_repository.save(village)
            
            # Save the troop to the database
            troop = await self.troops_repository.create(troop_data)
            if not troop:
                return {"success": False, "error": "Failed to create troop"}
            
            logger.info(f"Completed troop training task {task_id_param}, created troop {troop.id}")
            
            # Broadcast to all users since troop training affects the map for everyone
            await websocket_service.broadcast_troop_action_complete()
            
            return {"success": True, "troop_id": troop.id}
            
        except Exception as e:
            logger.error(f"Error completing troop training task {task_id_param}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {"success": False, "error": f"Error creating troops: {str(e)}"}
        
    async def complete_all_tasks_until(self, target_time: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Complete all pending tasks (constructions, troop training, and troop actions) 
        up to a specified time in chronological order of their completion times.
        
        Args:
            target_time: The time until which to complete tasks. If None, uses current time.
            
        Returns:
            Dict[str, Any]: Result statistics of the operation
        """
        if target_time is None:
            target_time = datetime.utcnow()
            
        logger.info(f"Completing all tasks until {target_time}")
        
        # Collect all pending tasks from different sources
        all_tasks = []
        stats = {
            "total_tasks_found": 0,
            "construction_tasks_completed": 0,
            "troop_training_tasks_completed": 0,
            "troop_action_tasks_completed": 0,
            "errors": []
        }
        
        try:
            # 1. Get all villages that might have pending tasks
            all_villages = await self.village_repository.get_all()
            if not all_villages:
                logger.info("No villages found when scheduling tasks")
                return stats
                
            logger.info(f"Found {len(all_villages)} villages to check for pending tasks")
            
            # 2. Collect construction tasks from all villages
            for village in all_villages:
                if not village:
                    continue
                    
                # Collect construction tasks
                if hasattr(village._data, 'construction_tasks'):
                    for task in village._data.construction_tasks:
                        if not task.processed and task.completion_time <= target_time:
                            all_tasks.append(TaskData(
                                task_id=task.id,
                                village_id=village.id,
                                completion_time=task.completion_time,
                                category=TaskCategory.CONSTRUCTION,
                                data=task
                            ))
                            stats["total_tasks_found"] += 1
                
                # Collect troop training tasks
                if hasattr(village._data, 'troop_training_tasks'):
                    for task in village._data.troop_training_tasks:
                        if not task.processed and task.completion_time <= target_time:
                            all_tasks.append(TaskData(
                                task_id=task.id,
                                village_id=village.id,
                                completion_time=task.completion_time,
                                category=TaskCategory.TROOP_TRAINING,
                                data=task
                            ))
                            stats["total_tasks_found"] += 1
            
            # 3. Collect troop action tasks that are pending
            troop_actions = await self.troop_action_repository.get_all_active()
            for action in troop_actions:
                if not action.processed and action.completion_time <= target_time:
                    all_tasks.append(TaskData(
                        task_id=action.id,
                        village_id="",  # Troop actions don't have a direct village ID
                        completion_time=action.completion_time,
                        category=TaskCategory.TROOP_ACTION,
                        data=action
                    ))
                    stats["total_tasks_found"] += 1
            
            # 4. Sort all tasks by completion time (earlier first)
            sorted_tasks = sorted(all_tasks, key=lambda x: x.completion_time)
            
            # 5. Execute tasks in chronological order
            for task in sorted_tasks:
                try:
                    if task.category == TaskCategory.CONSTRUCTION:
                        # Execute construction task
                        result = await self.complete_construction_task(
                            village_id=task.village_id,
                            task_id_param=task.task_id,
                            completion_time=task.completion_time
                        )
                        if result.get("success", False):
                            stats["construction_tasks_completed"] += 1
                        else:
                            stats["errors"].append(f"Failed to complete construction task {task.task_id}: {result.get('error', 'Unknown error')}")
                            
                    elif task.category == TaskCategory.TROOP_TRAINING:
                        # Execute troop training task
                        result = await self.complete_troop_training_task(
                            village_id=task.village_id,
                            task_id_param=task.task_id,
                            completion_time=task.completion_time
                        )
                        if result.get("success", False):
                            stats["troop_training_tasks_completed"] += 1
                        else:
                            stats["errors"].append(f"Failed to complete troop training task {task.task_id}: {result.get('error', 'Unknown error')}")
                            
                    elif task.category == TaskCategory.TROOP_ACTION:
                        # Execute troop action task
                        troop_action_service = self._get_troop_action_service()
                        result = await troop_action_service.complete_troop_action(
                            action_id=task.task_id,
                            completion_time=task.completion_time
                        )
                        if result.get("success", False):
                            stats["troop_action_tasks_completed"] += 1
                        else:
                            stats["errors"].append(f"Failed to complete troop action task {task.task_id}: {result.get('error', 'Unknown error')}")
                
                except Exception as task_error:
                    error_msg = f"Error completing task {task.task_id} of type {task.category}: {str(task_error)}"
                    logger.error(error_msg)
                    stats["errors"].append(error_msg)
                    
            # Calculate total completed tasks
            stats["total_tasks_completed"] = (
                stats["construction_tasks_completed"] + 
                stats["troop_training_tasks_completed"] + 
                stats["troop_action_tasks_completed"]
            )
            
            logger.info(f"Completed {stats['total_tasks_completed']} out of {stats['total_tasks_found']} tasks")
            if stats["errors"]:
                logger.warning(f"Encountered {len(stats['errors'])} errors while completing tasks")
                
            return stats
                
        except Exception as e:
            error_msg = f"Error in complete_all_tasks_until: {str(e)}"
            logger.error(error_msg)
            import traceback
            logger.error(traceback.format_exc())
            stats["errors"].append(error_msg)
            return stats
    
    # Helper validation methods that use existing services
    
    async def _validate_building_creation(self, village_id: str, building_type: ConstructionType, 
                                        slot: int) -> Dict[str, Any]:
        """Validate building creation parameters without creating the building"""
        village = await self.village_repository.get_by_id(village_id)
        if not village:
            return {"success": False, "error": "Village not found"}
            
        # Check if slot is available
        if village.get_building(slot):
            return {
                "success": False, 
                "error": f"Slot {slot} is already occupied"
            }
            
        # Check if there's already a pending task for this slot
        if hasattr(village._data, 'construction_tasks'):
            for task in village._data.construction_tasks:
                if not task.processed and task.slot == slot and (
                    task.task_type == TaskType.CREATE_BUILDING or task.task_type == TaskType.UPGRADE_BUILDING):
                    return {
                        "success": False, 
                        "error": f"There is already a pending building task for slot {slot}"
                    }
            
        # Check if we've reached the maximum number of buildings
        if len(village.get_all_buildings()) >= village.MAX_CONSTRUCTIONS:
            return {
                "success": False, 
                "error": f"Maximum number of buildings ({village.MAX_CONSTRUCTIONS}) reached"
            }
            
        # Check if we can afford the building
        from minute_empire.domain.building import Building
        if not Building.can_create(building_type, village):
            costs = Building.get_creation_cost(building_type)
            missing = {
                resource: amount - getattr(village.resources, resource, 0)
                for resource, amount in costs.items()
                if getattr(village.resources, resource, 0) < amount
            }
            return {
                "success": False, 
                "error": "Insufficient resources",
                "cost": costs,
                "missing": missing,
                "current_resources": {
                    "wood": village.resources.wood,
                    "stone": village.resources.stone,
                    "iron": village.resources.iron,
                    "food": village.resources.food
                }
            }
            
        # Check if there's enough spare population (level 1 for new buildings)
        total_population = village.getTotalPopulation()
        working_population = village.getWorkingPopulation()
        spare_population = total_population - working_population
        
        if spare_population < 1:
            return {
                "success": False,
                "error": "Insufficient spare population",
                "required": 1,
                "available": spare_population,
                "total_population": total_population,
                "working_population": working_population
            }
            
        # Validation passed successfully - no resource deduction here
        return {"success": True}
        
    async def _validate_field_creation(self, village_id: str, field_type: ResourceFieldType, 
                                     slot: int) -> Dict[str, Any]:
        """Validate resource field creation parameters without creating the field"""
        village = await self.village_repository.get_by_id(village_id)
        if not village:
            return {"success": False, "error": "Village not found"}
            
        # Check if slot is available
        if village.get_resource_field(slot):
            return {
                "success": False, 
                "error": f"Slot {slot} is already occupied"
            }
            
        # Check if there's already a pending task for this slot
        if hasattr(village._data, 'construction_tasks'):
            for task in village._data.construction_tasks:
                if not task.processed and task.slot == slot and (
                    task.task_type == TaskType.CREATE_FIELD or task.task_type == TaskType.UPGRADE_FIELD):
                    return {
                        "success": False, 
                        "error": f"There is already a pending resource field task for slot {slot}"
                    }
            
        # Check if we've reached the maximum number of fields
        if len(village.get_all_resource_fields()) >= village.MAX_FIELDS:
            return {
                "success": False, 
                "error": f"Maximum number of fields ({village.MAX_FIELDS}) reached"
            }

        # Find village center to check its level
        village_center = None
        for building in village.get_all_buildings():
            if building.type == ConstructionType.CITY_CENTER:
                village_center = building
                break
        
        # Define slot restrictions based on village center level
        restricted_slots = {
            1: [0, 1, 2, 3, 4, 5, 6, 7],
            3: [0, 1, 2, 3, 4, 5, 6, 7, 11, 12, 13],
            5: [0, 1, 2, 3, 4, 5, 6, 7, 11, 12, 13, 17, 18, 19],
            7: [0, 1, 2, 3, 4, 5, 6, 7, 11, 12, 13, 17, 18, 19, 8, 9, 10],
            9: [0, 1, 2, 3, 4, 5, 6, 7, 11, 12, 13, 17, 18, 19, 8, 9, 10, 14, 15, 16]
        }
        
        # Check if the requested slot is restricted
        for required_level, slots in restricted_slots.items():
            if slot in slots:
                # If village center doesn't exist or its level is too low
                if not village_center or village_center.level < required_level:
                    return {
                        "success": False,
                        "error": f"Resource field in slot {slot} requires Village Center level {required_level}",
                        "required_village_center_level": required_level,
                        "current_village_center_level": village_center.level if village_center else 0
                    }
                break
            
        # Check if we can afford the field
        from minute_empire.domain.resource_field import ResourceProducer
        if not ResourceProducer.can_create(field_type, village):
            costs = ResourceProducer.get_creation_cost(field_type)
            missing = {
                resource: amount - getattr(village.resources, resource, 0)
                for resource, amount in costs.items()
                if getattr(village.resources, resource, 0) < amount
            }
            return {
                "success": False, 
                "error": "Insufficient resources",
                "cost": costs,
                "missing": missing,
                "current_resources": {
                    "wood": village.resources.wood,
                    "stone": village.resources.stone,
                    "iron": village.resources.iron,
                    "food": village.resources.food
                }
            }
            
        # Check if there's enough spare population (level 1 for new fields)
        total_population = village.getTotalPopulation()
        working_population = village.getWorkingPopulation()
        spare_population = total_population - working_population
        
        if spare_population < 1:
            return {
                "success": False,
                "error": "Insufficient spare population",
                "required": 1,
                "available": spare_population,
                "total_population": total_population,
                "working_population": working_population
            }
            
        # Validation passed successfully - no resource deduction here
        return {"success": True}
        
    async def _validate_building_upgrade(self, village_id: str, slot: int) -> Dict[str, Any]:
        """Validate building upgrade parameters without upgrading the building"""
        village = await self.village_repository.get_by_id(village_id)
        if not village:
            return {"success": False, "error": "Village not found"}
            
        # Get the building
        building = village.get_building(slot)
        if not building:
            return {"success": False, "error": f"No building found in slot {slot}"}
            
        # Check if there's already a pending upgrade task for this building
        if hasattr(village._data, 'construction_tasks'):
            for task in village._data.construction_tasks:
                if not task.processed and task.slot == slot and task.task_type == TaskType.UPGRADE_BUILDING:
                    return {
                        "success": False, 
                        "error": f"There is already a pending upgrade task for building in slot {slot}"
                    }
            
        # Check if we can afford the upgrade
        if not building.can_upgrade():
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
            
        # Check if there's enough spare population for the upgrade
        total_population = village.getTotalPopulation()
        working_population = village.getWorkingPopulation()
        spare_population = total_population - working_population
        
        # For upgrades, we need enough spare population for the target level
        target_level = building.level + 1
        if spare_population < round(target_level**2):
            return {
                "success": False,
                "error": "Insufficient spare population",
                "required": round(target_level**2),
                "available": spare_population,
                "total_population": total_population,
                "working_population": working_population
            }
            
        # Validation passed successfully - no resource deduction here
        return {"success": True}
        
    async def _validate_field_upgrade(self, village_id: str, slot: int) -> Dict[str, Any]:
        """Validate field upgrade parameters without upgrading the field"""
        village = await self.village_repository.get_by_id(village_id)
        if not village:
            return {"success": False, "error": "Village not found"}
            
        # Get the field
        field = village.get_resource_field(slot)
        if not field:
            return {"success": False, "error": f"No resource field found in slot {slot}"}
            
        # Check if there's already a pending upgrade task for this field
        if hasattr(village._data, 'construction_tasks'):
            for task in village._data.construction_tasks:
                if not task.processed and task.slot == slot and task.task_type == TaskType.UPGRADE_FIELD:
                    return {
                        "success": False, 
                        "error": f"There is already a pending upgrade task for field in slot {slot}"
                    }
            
        # Check if we can afford the upgrade
        if not field.can_upgrade():
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
            
        # Check if there's enough spare population for the upgrade
        total_population = village.getTotalPopulation()
        working_population = village.getWorkingPopulation()
        spare_population = total_population - working_population
        
        # For upgrades, we need enough spare population for the target level
        target_level = field.level + 1
        if spare_population < round(target_level**2):
            return {
                "success": False,
                "error": "Insufficient spare population",
                "required": round(target_level**2),
                "available": spare_population,
                "total_population": total_population,
                "working_population": working_population
            }
            
        # Validation passed successfully - no resource deduction here
        return {"success": True}
        
    async def _validate_troop_training(self, village_id: str, troop_type: TroopType, quantity: int) -> Dict[str, Any]:
        """Validate troop training parameters without training the troops"""
        village = await self.village_repository.get_by_id(village_id)
        if not village:
            return {"success": False, "error": "Village not found"}
            
        # Check if there's already a pending training task for this troop
        if hasattr(village._data, 'troop_training_tasks'):
            for task in village._data.troop_training_tasks:
                if not task.processed and task.troop_type == troop_type.value:
                    return {
                        "success": False, 
                        "error": f"There is already a pending troop training task for troop type {troop_type.value}"
                    }
            
        # Check if we can afford the training
        costs = Troop.get_training_cost(troop_type, quantity)
        if not village.deduct_resources(costs):
            return {
                "success": False, 
                "error": "Insufficient resources",
                "cost": costs
            }
            
        # Check if there's enough spare population for the training
        total_population = village.getTotalPopulation()
        working_population = village.getWorkingPopulation()
        spare_population = total_population - working_population
        
        # For training, we need enough spare population for the quantity
        if spare_population < quantity:
            return {
                "success": False,
                "error": "Insufficient spare population",
                "required": quantity,
                "available": spare_population,
                "total_population": total_population,
                "working_population": working_population
            }
            
        # Validation passed successfully - no resource deduction here
        return {"success": True}

    async def schedule_pending_tasks(self, after_time: datetime) -> Dict[str, Any]:
        """
        Schedule all pending tasks that are due after the specified time.
        This function scans for all pending construction tasks, troop training tasks, 
        and troop actions across all villages and schedules them for execution.
        
        Args:
            after_time: Schedule only tasks that are due after this time
            
        Returns:
            Dict with statistics about scheduled tasks
        """
        logger.info(f"Scheduling pending tasks due after {after_time}")
        
        result = {
            "construction_tasks_scheduled": 0,
            "troop_training_tasks_scheduled": 0,
            "troop_action_tasks_scheduled": 0,
            "total_tasks_scheduled": 0,
            "errors": []
        }
        
        # Initialize services and repositories
        from minute_empire.repositories.village_repository import VillageRepository
        from minute_empire.repositories.troop_action_repository import TroopActionRepository
        village_repository = VillageRepository()
        troop_action_repo = TroopActionRepository()
        
        try:
            # 1. Get all villages that might have pending tasks
            all_villages = await village_repository.get_all()
            if not all_villages:
                logger.info("No villages found when scheduling tasks")
                return result
            
            logger.info(f"Found {len(all_villages)} villages to check for pending future tasks")
            
            # 2. Process villages to find all pending future tasks
            for village in all_villages:
                if not village:
                    continue
                    
                # A. Schedule construction tasks (buildings and fields)
                if hasattr(village._data, 'construction_tasks'):
                    construction_count = 0
                    for task in village._data.construction_tasks:
                        if not task.processed and task.completion_time > after_time:
                            # Schedule the task based on type
                            await task_scheduler.schedule_task(
                                task_id=task.id,
                                execution_time=task.completion_time,
                                callback=self.complete_construction_task,
                                village_id=village.id,
                                task_id_param=task.id,
                                completion_time=task.completion_time
                            )
                            construction_count += 1
                            result["total_tasks_scheduled"] += 1
                            result["construction_tasks_scheduled"] += 1
                    
                    if construction_count > 0:
                        logger.info(f"Scheduled {construction_count} future construction tasks for village {village.id}")
                
                # B. Schedule troop training tasks
                if hasattr(village._data, 'troop_training_tasks'):
                    training_count = 0
                    for task in village._data.troop_training_tasks:
                        if not task.processed and task.completion_time > after_time:
                            # Schedule the troop training task
                            await task_scheduler.schedule_task(
                                task_id=task.id,
                                execution_time=task.completion_time,
                                callback=self.complete_troop_training_task,
                                village_id=village.id,
                                task_id_param=task.id,
                                completion_time=task.completion_time
                            )
                            training_count += 1
                            result["total_tasks_scheduled"] += 1
                            result["troop_training_tasks_scheduled"] += 1
                    
                    if training_count > 0:
                        logger.info(f"Scheduled {training_count} future troop training tasks for village {village.id}")
            
            # 3. Schedule troop action tasks (movements and attacks)
            pending_actions = await troop_action_repo.get_pending_actions()
            
            action_count = 0
            troop_action_service = self._get_troop_action_service()
            
            for action in pending_actions:
                if not action.processed and action.completion_time > after_time:
                    # Schedule future actions
                    await task_scheduler.schedule_task(
                        task_id=action.id,
                        execution_time=action.completion_time,
                        callback=troop_action_service.complete_troop_action,
                        action_id=action.id,
                        completion_time=action.completion_time
                    )
                    action_count += 1
                    result["total_tasks_scheduled"] += 1
                    result["troop_action_tasks_scheduled"] += 1
            
            if action_count > 0:
                logger.info(f"Scheduled {action_count} future troop action tasks")
            
            logger.info(f"Total scheduled future tasks: {result['total_tasks_scheduled']}")
            
        except Exception as e:
            error_msg = f"Error scheduling pending tasks: {str(e)}"
            logger.error(error_msg)
            import traceback
            logger.error(traceback.format_exc())
            result["errors"].append(error_msg)
        
        return result 

    async def start_building_destruction(self, village_id: str, slot: int) -> Dict[str, Any]:
        """
        Start timed building destruction.
        
        Args:
            village_id: The ID of the village
            slot: Slot of the building to destroy
            
        Returns:
            Dict[str, Any]: Result of the operation
        """
        # Validate destruction first
        validation_result = await self._validate_building_destruction(village_id, slot)
        if not validation_result["success"]:
            return validation_result
            
        # Get the village and building after validation
        village = await self.village_repository.get_by_id(village_id)
        building = village.get_building(slot)
        
        # Deduct resources for the task (costs were already validated in _validate_building_destruction)
        costs = building.get_upgrade_cost()
        village.deduct_resources(costs)
            
        # Get the destruction time in minutes (same as upgrade time or creation time if level 1)
        if building.level == 1:
            duration = Building.get_creation_time(building.type)
        else:
            duration = building.get_upgrade_time()
        
        # Create task
        task = village.add_construction_task(
            TaskType.DESTROY_BUILDING,
            building.type.value,
            slot,
            duration
        )
        
        # Save changes
        await self.village_repository.save(village)
        
        # Schedule the task completion
        await task_scheduler.schedule_task(
            task_id=task.id,
            execution_time=task.completion_time,
            callback=self.complete_construction_task,
            village_id=village_id,
            task_id_param=task.id,
            completion_time=task.completion_time
        )
        
        return {
            "success": True,
            "building_type": building.type.value,
            "level": building.level,
            "slot": slot,
            "estimated_completion": task.completion_time,
            "task_id": task.id
        }
        
    async def start_field_destruction(self, village_id: str, slot: int) -> Dict[str, Any]:
        """
        Start timed field destruction.
        
        Args:
            village_id: The ID of the village
            slot: Slot of the field to destroy
            
        Returns:
            Dict[str, Any]: Result of the operation
        """
        # Validate destruction first
        validation_result = await self._validate_field_destruction(village_id, slot)
        if not validation_result["success"]:
            return validation_result
            
        # Get the village and field after validation
        village = await self.village_repository.get_by_id(village_id)
        field = village.get_resource_field(slot)
        
        # Deduct resources for the task (costs were already validated in _validate_field_destruction)
        costs = field.get_upgrade_cost()
        village.deduct_resources(costs)
            
        # Get the destruction time in minutes (same as upgrade time or creation time if level 1)
        if field.level == 1:
            duration = ResourceProducer.get_creation_time(field.type)
        else:
            duration = field.get_upgrade_time()
        
        # Create task
        task = village.add_construction_task(
            TaskType.DESTROY_FIELD,
            field.type.value,
            slot,
            duration
        )
        
        # Save changes
        await self.village_repository.save(village)
        
        # Schedule the task completion
        await task_scheduler.schedule_task(
            task_id=task.id,
            execution_time=task.completion_time,
            callback=self.complete_construction_task,
            village_id=village_id,
            task_id_param=task.id,
            completion_time=task.completion_time
        )
        
        return {
            "success": True,
            "field_type": field.type.value,
            "level": field.level,
            "slot": slot,
            "estimated_completion": task.completion_time,
            "task_id": task.id
        }
    
    async def _validate_building_destruction(self, village_id: str, slot: int) -> Dict[str, Any]:
        """
        Validate if a building can be destroyed.
        
        Args:
            village_id: The ID of the village
            slot: Slot of the building to destroy
            
        Returns:
            Dict[str, Any]: Validation result with success flag and error message
        """
        # Get the village
        village = await self.village_repository.get_by_id(village_id)
        if not village:
            return {
                "success": False,
                "error": "Village not found"
            }
            
        # Check if the building exists in the given slot
        building = village.get_building(slot)
        if not building:
            return {
                "success": False,
                "error": f"No building exists in slot {slot}"
            }
            
        # Check if there is already a task for this building
        if hasattr(village._data, 'construction_tasks'):
            for task in village._data.construction_tasks:
                if not task.processed and task.slot == slot:
                    return {
                        "success": False,
                        "error": f"There is already an ongoing task for the building in slot {slot}"
                    }
        
        # Check if there are sufficient resources for the task
        costs = building.get_upgrade_cost()
        for resource, amount in costs.items():
            current = getattr(village.resources, resource, 0)
            if current < amount:
                return {
                    "success": False,
                    "error": f"Insufficient {resource}",
                    "cost": costs
                }
                    
        return {
            "success": True,
            "cost": costs  # Include the cost in the result for reference
        }
    
    async def _validate_field_destruction(self, village_id: str, slot: int) -> Dict[str, Any]:
        """
        Validate if a resource field can be destroyed.
        
        Args:
            village_id: The ID of the village
            slot: Slot of the field to destroy
            
        Returns:
            Dict[str, Any]: Validation result with success flag and error message
        """
        # Get the village
        village = await self.village_repository.get_by_id(village_id)
        if not village:
            return {
                "success": False,
                "error": "Village not found"
            }
            
        # Check if the field exists in the given slot
        field = village.get_resource_field(slot)
        if not field:
            return {
                "success": False,
                "error": f"No resource field exists in slot {slot}"
            }
            
        # Check if there is already a task for this field
        if hasattr(village._data, 'construction_tasks'):
            for task in village._data.construction_tasks:
                if not task.processed and task.slot == slot:
                    return {
                        "success": False,
                        "error": f"There is already an ongoing task for the field in slot {slot}"
                    }
        
        # Check if there are sufficient resources for the task
        costs = field.get_upgrade_cost()
        for resource, amount in costs.items():
            current = getattr(village.resources, resource, 0)
            if current < amount:
                return {
                    "success": False,
                    "error": f"Insufficient {resource}",
                    "cost": costs
                }
                    
        return {
            "success": True,
            "cost": costs  # Include the cost in the result for reference
        } 