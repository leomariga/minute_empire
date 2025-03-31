from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from minute_empire.schemas.schemas import VillageInDB, ConstructionType, ResourceFieldType
from minute_empire.schemas.schemas import TaskType, ConstructionTask, Construction, ResourceField
from minute_empire.domain.building import Building
from minute_empire.domain.resource_field import ResourceProducer
from bson import ObjectId

class Village:
    """Domain class for villages with game logic"""
    # Class constants from core.village
    MAX_FIELDS = 20
    MAX_CONSTRUCTIONS = 25
    
    def __init__(self, village_data: VillageInDB):
        self._data = village_data
        self._changed = False
        self._buildings = None
        self._resource_fields = None
        
    
    @property
    def id(self) -> str:
        """Village ID"""
        return self._data.id
        
    @property
    def name(self) -> str:
        """Village name"""
        return self._data.name
    
    @property
    def owner_id(self) -> str:
        """Owner's user ID"""
        return self._data.owner_id
    
    @property
    def location(self) -> Dict[str, int]:
        """Village location"""
        return {"x": self._data.location.x, "y": self._data.location.y}
    
    @property
    def resources(self):
        """Access to resources"""
        return self._data.resources
    
    @property
    def city(self):
        """City object"""
        return self._data.city
    
    @property
    def created_at(self) -> datetime:
        """Village creation time"""
        return self._data.created_at
    
    @property
    def updated_at(self) -> datetime:
        """Last update time"""
        return self._data.updated_at
    
    @property
    def res_update_at(self) -> datetime:
        """Last resource update time"""
        return self._data.res_update_at
    
    @res_update_at.setter
    def res_update_at(self, value: datetime) -> None:
        """Set last resource update time"""
        self._data.res_update_at = value
    
    def get_building(self, slot: int) -> Optional[Building]:
        """Get building by slot number"""
        # Lazy-load buildings
        if self._buildings is None:
            self._buildings = {}
            
            # Add wall as special case
            if self._data.city.wall:
                wall = Building(self._data.city.wall, self)
                self._buildings[wall.slot] = wall
            
            # Add other buildings
            for construction in self._data.city.constructions:
                building = Building(construction, self)
                self._buildings[building.slot] = building
                
        return self._buildings.get(slot)
    
    def get_all_buildings(self) -> List[Building]:
        """Get all buildings"""
        # Ensure buildings are loaded
        if self._buildings is None:
            # This will load the buildings
            # We need to load at least one building to load the list
            self.get_building(0)
            
        return list(self._buildings.values())
    
    def get_resource_field(self, slot: int) -> Optional[ResourceProducer]:
        """Get resource field by slot number"""
        # Lazy-load resource fields
        if self._resource_fields is None:
            self._resource_fields = {}
            # Load all resource fields into cache
            if hasattr(self._data, 'resource_fields') and self._data.resource_fields:
                for field in self._data.resource_fields:
                    if field is not None and hasattr(field, 'slot'):
                        producer = ResourceProducer(field, self)
                        self._resource_fields[field.slot] = producer
        
        return self._resource_fields.get(slot)
    
    def get_all_resource_fields(self) -> List[ResourceProducer]:
        """Get all resource fields"""
        # Ensure resource fields are loaded
        if self._resource_fields is None:
            # This will load the resource fields
            # We need to load at least one resource field to load the list
            self.get_resource_field(0)
        
        return list(self._resource_fields.values())
    
    def get_production_bonus_for_resource(self, resource_type: str) -> float:
        """Calculate production bonus for a resource type from all buildings"""
        bonus = 0.0
        for building in self.get_all_buildings():
            # Get bonus dictionary from building and extract the specific resource value
            building_bonuses = building.get_production_bonus()
            if resource_type in building_bonuses:
                bonus += building_bonuses[resource_type]
        return bonus
    
    def get_resource_rates(self) -> Dict[str, float]:
        """Calculate hourly production rates for all resources"""
        rates = {
            "wood": 9999,
            "stone": 9999, 
            "iron": 9999,
            "food": 9999
        }
        
        # Check if resource fields exist and are initialized
        if not hasattr(self, '_resource_fields') or self._resource_fields is None:
            try:
                # Attempt to load resource fields
                self.get_all_resource_fields()
                # If still None or empty, return default rates
                if not self._resource_fields:
                    return rates
            except Exception:
                # If loading fails, return default rates
                return rates
        
        # Sum up production from all fields (safely)
        try:
            for field in self.get_all_resource_fields():
                # Get production rates dictionary from the field
                field_rates = field.get_production_rate()
                
                # Add each resource rate to the total rates
                for resource_type, rate in field_rates.items():
                    if rate > 0 and resource_type in rates:
                        rates[resource_type] += rate
        except Exception:
            # If any error occurs during calculation, use the defaults
            pass
            
        return rates
    
    def update_resources(self, time_elapsed_hours: float) -> None:
        """Update resources based on production rates and time elapsed"""
        rates = self.get_resource_rates()
        
        for resource_type, rate in rates.items():
            # Calculate production
            produced = rate * time_elapsed_hours
            
            # Get current amount
            current = getattr(self._data.resources, resource_type, 0)
            
            # Calculate storage capacity
            capacity = self.calculate_storage_capacity(resource_type)
            
            # Update resource (don't exceed capacity)
            setattr(self._data.resources, resource_type, 
                   min(current + produced, capacity))
        
        self.mark_as_changed()
    
    def calculate_storage_capacity(self, resource_type: str) -> int:
        """Calculate storage capacity based on warehouse/granary levels"""
        base_capacity = 1000
        
        if resource_type == "food":
            # Find granary
            granary = next((b for b in self.get_all_buildings()
                          if b.type == ConstructionType.GRANARY), None)
            if granary:
                return base_capacity * (1 + 0.3 * granary.level)
        else:
            # Find warehouse for other resources
            warehouse = next((b for b in self.get_all_buildings()
                            if b.type == ConstructionType.WAREHOUSE), None)
            if warehouse:
                return base_capacity * (1 + 0.3 * warehouse.level)
                
        return base_capacity
    
    def mark_as_changed(self) -> None:
        """Mark that this village needs to be saved to database"""
        self._changed = True
        # Update the timestamp
        self._data.updated_at = datetime.utcnow()
    
    def has_changes(self) -> bool:
        """Check if village has unsaved changes"""
        return self._changed
    
    def deduct_resources(self, costs: Dict[str, int]) -> bool:
        """
        Deduct resources from the village and mark it as changed.
        
        Args:
            costs: Dictionary of resource costs to deduct
            
        Returns:
            bool: True if deduction was successful, False if insufficient resources
        """
        # Check if we have enough resources
        for resource, amount in costs.items():
            current = getattr(self.resources, resource, 0)
            if current < amount:
                return False
                
        # Deduct resources
        for resource, amount in costs.items():
            current = getattr(self.resources, resource, 0)
            setattr(self.resources, resource, current - amount)
            
        # Mark as changed
        self.mark_as_changed()
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert village to dictionary for storage or API responses"""
        return self._data.dict(by_alias=True)

    def add_construction_task(self, task_type: TaskType, target_type: str, 
                            slot: int, duration_minutes: int) -> ConstructionTask:
        """
        Add a new construction task to the village.
        
        Args:
            task_type: Type of task (create or upgrade)
            target_type: Type of building or field
            slot: Slot number
            duration_minutes: How long the task takes to complete
            
        Returns:
            ConstructionTask: The newly created task
        """
        # Make sure we have a construction_tasks list
        if not hasattr(self._data, 'construction_tasks'):
            self._data.construction_tasks = []
            
        # Create the task
        now = datetime.utcnow()
        completion_time = now + timedelta(minutes=duration_minutes)
        
        task = ConstructionTask(
            id=str(ObjectId()),
            task_type=task_type,
            target_type=target_type,
            slot=slot,
            started_at=now,
            completion_time=completion_time
        )
        
        # Add to village data
        self._data.construction_tasks.append(task)
        
        # Mark as changed
        self.mark_as_changed()
        
        return task
    
    def process_construction_tasks(self) -> List[ConstructionTask]:
        """
        Process all completed construction tasks.
        
        Returns:
            List[ConstructionTask]: List of tasks that were completed
        """
        if not hasattr(self._data, 'construction_tasks'):
            return []
            
        now = datetime.utcnow()
        completed_tasks = []
        
        for task in self._data.construction_tasks:
            # Skip already processed tasks
            if task.processed:
                continue
                
            # Check if task is complete
            if task.completion_time <= now:
                # Complete the task
                self.complete_construction_task(task)
                completed_tasks.append(task)
                
        return completed_tasks
    
    def complete_construction_task(self, task: ConstructionTask) -> None:
        """
        Complete a construction task by creating or upgrading the target.
        
        Args:
            task: The task to complete
        """
        from minute_empire.schemas.schemas import ResourceFieldType, ConstructionType
        
        # Mark as processed
        task.processed = True
        
        # Handle different task types
        if task.task_type == TaskType.CREATE_BUILDING:
            # Convert string to enum
            building_type = ConstructionType(task.target_type)
            
            # Create construction directly without resource check
            # (resources were already deducted when the task was created)
            construction = Construction(
                type=building_type,
                level=1,
                slot=task.slot
            )
            
            # Add to village constructions
            self._data.city.constructions.append(construction)
            
            # Clear building cache
            self._buildings = None
            print(f"[Village] Completed building creation: {building_type.value} in slot {task.slot}")
                
        elif task.task_type == TaskType.UPGRADE_BUILDING:
            # Find the building
            building = self.get_building(task.slot)
            if building:
                # Just set the level directly without calling upgrade()
                # (which would check and deduct resources again)
                building.data.level = task.level
                
                # Clear building cache
                self._buildings = None
                print(f"[Village] Completed building upgrade: {building.type.value} to level {task.level}")
            else:
                print(f"[Village] Failed to complete building upgrade task: Building not found in slot {task.slot}")
                
        elif task.task_type == TaskType.CREATE_FIELD:
            # Convert string to enum
            field_type = ResourceFieldType(task.target_type)
            
            # Create field directly without resource check
            # (resources were already deducted when the task was created)
            field = ResourceField(
                type=field_type,
                level=1,
                slot=task.slot
            )
            
            # Add to village fields
            self._data.resource_fields.append(field)
            
            # Clear resource field cache
            self._resource_fields = None
            print(f"[Village] Completed field creation: {field_type.value} in slot {task.slot}")
                
        elif task.task_type == TaskType.UPGRADE_FIELD:
            # Find the field
            field = self.get_resource_field(task.slot)
            if field:
                # Just set the level directly without calling upgrade()
                # (which would check and deduct resources again)
                field.data.level = task.level
                
                # Clear resource field cache
                self._resource_fields = None
                print(f"[Village] Completed field upgrade: {field.type.value} to level {task.level}")
            else:
                print(f"[Village] Failed to complete field upgrade task: Field not found in slot {task.slot}")
                
        # Mark village as changed
        self.mark_as_changed()

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the village for display"""
        # Process any completed construction tasks first
        self.process_construction_tasks()
        
        # Get production rates (now safely handled within the method)
        production_rates = self.get_resource_rates()
        
        # Safely get building and resource field counts
        building_count = 0
        resource_fields_count = 0
        
        try:
            building_count = len(self.get_all_buildings())
        except Exception:
            pass
            
        try:
            resource_fields_count = len(self.get_all_resource_fields())
            print(f"[Village] Resource fields count: {resource_fields_count}")
        except Exception:
            pass
        
        # Safely get resource fields serialized
        resources_fields_list = []
        try:
            for field in self.get_all_resource_fields():
                print(f"[Village] Resource field: {field}")
                if hasattr(field, 'to_dict') and callable(field.to_dict):
                    print(f"[Village] Resource field to dict: {field.to_dict()}")
                    resources_fields_list.append(field.to_dict())
        except Exception:
            pass
            
        # Safely get city data
        city_dict = {}
        try:
            if hasattr(self.city, 'dict') and callable(self.city.dict):
                city_dict = self.city.dict()
            elif hasattr(self.city, 'to_dict') and callable(self.city.to_dict):
                city_dict = self.city.to_dict()
        except Exception:
            pass
            
        # Get pending construction tasks
        now = datetime.utcnow()
        pending_tasks = []
        
        if hasattr(self._data, 'construction_tasks'):
            for task in self._data.construction_tasks:
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
            
        # Basic village info with safe resource access
        return {
            "id": self.id,
            "name": self.name,
            "location": self.location,
            "owner_id": self.owner_id,
            "resources": {
                "wood": self.resources.wood,
                "stone": self.resources.stone,
                "iron": self.resources.iron,
                "food": self.resources.food
            },
            "resources_fields": resources_fields_list,
            "city": city_dict,
            "production_rates": production_rates,
            "building_count": building_count,
            "resource_fields_count": resource_fields_count,
            "construction_tasks": pending_tasks,
            "res_update_at": self.res_update_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    def __str__(self) -> str:
        return f"Village: {self.name} at {self.location}"