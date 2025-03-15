from datetime import datetime
from typing import Dict, List, Optional, Any
from minute_empire.schemas.schemas import VillageInDB, ConstructionType, ResourceFieldType
from minute_empire.domain.building import Building
from minute_empire.domain.resource import ResourceProducer

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
            self.get_building(0)
            
        return list(self._buildings.values())
    
    def get_resource_field(self, slot: int) -> Optional[ResourceProducer]:
        """Get resource field by slot number"""
        # Lazy-load resource fields
        if self._resource_fields is None:
            self._resource_fields = {}
            for field in self._data.resource_fields:
                producer = ResourceProducer(field, self)
                self._resource_fields[field.slot] = producer
                
        return self._resource_fields.get(slot)
    
    def get_all_resource_fields(self) -> List[ResourceProducer]:
        """Get all resource fields"""
        # Ensure resource fields are loaded
        if self._resource_fields is None:
            self._resource_fields = {}
            # Make sure resource fields exist in the data
            if hasattr(self._data, 'resource_fields') and self._data.resource_fields:
                try:
                    # This will load the resource fields
                    for field in self._data.resource_fields:
                        if field is not None and hasattr(field, 'slot'):
                            self.get_resource_field(field.slot)
                except Exception as e:
                    print(f"Error loading resource fields: {str(e)}")
            
        # Just in case _resource_fields is None after all attempts
        if self._resource_fields is None:
            self._resource_fields = {}
            
        try:
            return list(self._resource_fields.values())
        except Exception as e:
            print(f"Error getting resource_fields values: {str(e)}")
            return []
    
    def get_production_bonus_for_resource(self, resource_type: str) -> float:
        """Calculate production bonus for a resource type from all buildings"""
        bonus = 0.0
        for building in self.get_all_buildings():
            bonus += building.get_production_bonus(resource_type)
        return bonus
    
    def get_resource_rates(self) -> Dict[str, float]:
        """Calculate hourly production rates for all resources"""
        rates = {
            "wood": 600,
            "stone": 600, 
            "iron": 600,
            "food": 600
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
                resource_type = field.type.value  # Convert enum to string
                rates[resource_type] += field.production_rate
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
            capacity = self._calculate_storage_capacity(resource_type)
            
            # Update resource (don't exceed capacity)
            setattr(self._data.resources, resource_type, 
                   min(current + produced, capacity))
        
        self.mark_as_changed()
    
    def _calculate_storage_capacity(self, resource_type: str) -> int:
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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert village to dictionary for storage or API responses"""
        return self._data.dict(by_alias=True)

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the village for display"""
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
        except Exception:
            pass
        
        # Safely get resource fields serialized
        resources_fields_list = []
        try:
            for field in self.get_all_resource_fields():
                if hasattr(field, 'to_dict') and callable(field.to_dict):
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
            "res_update_at": self.res_update_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    def __str__(self) -> str:
        return f"Village: {self.name} at {self.location}" 