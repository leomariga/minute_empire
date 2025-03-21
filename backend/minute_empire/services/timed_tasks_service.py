from datetime import datetime
from typing import Dict, List, Optional, Any
from minute_empire.repositories.village_repository import VillageRepository
from minute_empire.schemas.schemas import TaskType, ConstructionTask 
from minute_empire.schemas.schemas import ConstructionType, ResourceFieldType
from minute_empire.services.building_service import BuildingService
from minute_empire.services.resource_field_service import ResourceFieldService
from minute_empire.domain.resource_field import ResourceProducer
from minute_empire.domain.building import Building
class TimedConstructionService:
    """
    Service for managing timed construction of buildings and fields.
    Acts as a coordinator between domain objects and existing services.
    """
    
    def __init__(self):
        self.village_repository = VillageRepository()
        self.building_service = BuildingService()
        self.resource_field_service = ResourceFieldService()
    
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
        
        return {
            "success": True,
            "field_type": field.type.value,
            "old_level": field.level,
            "new_level": field.level + 1,
            "slot": slot,
            "estimated_completion": task.completion_time,
            "task_id": task.id
        }
        
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
            
        # Validation passed successfully - no resource deduction here
        return {"success": True} 