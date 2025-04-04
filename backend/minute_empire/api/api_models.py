from pydantic import BaseModel, Field, validator
import re
from typing import Optional, List, Dict
from minute_empire.schemas.schemas import Location, ResourceField, City, Construction, ConstructionType, TaskType, ConstructionTask

# Pydantic model for registration request
class RegistrationRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="User's username")
    password: str = Field(..., min_length=8, description="User's password")
    family_name: str = Field(..., min_length=2, max_length=50, description="User's family name")
    color: str = Field(..., description="Hex color code for the user")
    village_name: str = Field(..., min_length=3, max_length=50, description="Name for the user's first village")

    # Validator for color field to ensure it's a valid hex color
    @validator('color')
    def validate_color(cls, v):
        if not re.match(r'^#[0-9a-fA-F]{6}$', v):
            raise ValueError('Color must be a valid hex color code (e.g., #FF0000)')
        return v

# Pydantic model for registration response
class RegistrationResponse(BaseModel):
    message: str
    user_id: str
    village_id: str

# Authentication models
class LoginRequest(BaseModel):
    username: str = Field(..., description="User's username")
    password: str = Field(..., description="User's password")

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str
    family_name: str

# User models
class UserBase(BaseModel):
    username: str
    family_name: str
    color: str

class UserResponse(UserBase):
    id: str

# User basic info model for map display
class UserBasicInfo(BaseModel):
    id: str = Field(..., description="User's ID")
    family_name: str = Field(..., description="User's family name")
    color: str = Field(..., description="User's color code")

# Village models
class VillageResponse(BaseModel):
    id: str
    name: str
    location: Location
    owner_id: str
    resource_fields: List[ResourceField]
    city: City
    created_at: str

# Command models
class CommandRequest(BaseModel):
    command: str = Field(..., description="Command string to execute")
    village_id: str = Field(..., description="ID of the village to execute the command on")

class CommandResponse(BaseModel):
    success: bool
    message: str
    data: dict = {}

# Resource and Production Info Models
class ResourceInfo(BaseModel):
    current: float = Field(..., description="Current amount of the resource")
    rate: float = Field(..., description="Current production rate per hour")
    capacity: float = Field(..., description="Maximum storage capacity")

class ResourceFieldsInfo(ResourceField):
    current_production_rate: Dict[str, float] = Field(..., description="Current production rates per hour for each resource type")
    upgrade_cost: Dict[str, int] = Field(..., description="Resource costs to upgrade to next level")
    upgrade_time: int = Field(..., description="Time in minutes to upgrade to next level")
    next_level_production_rate: Dict[str, float] = Field(..., description="Production rates at next level for each resource type")

class ConstructionInfo(Construction):
    production_bonus: Dict[str, float] = Field(..., description="Current production bonuses provided by the building for each resource type")
    upgrade_cost: Dict[str, int] = Field(..., description="Resource costs to upgrade to next level")
    upgrade_time: int = Field(..., description="Time in minutes to upgrade to next level")
    next_level_bonus: Dict[str, float] = Field(..., description="Production bonuses at next level for each resource type")

class CityInfo(BaseModel):
    wall: Optional[ConstructionInfo] = None
    constructions: List[ConstructionInfo] = Field(default_factory=list)

# Map models
class MapBounds(BaseModel):
    x_min: int
    x_max: int
    y_min: int
    y_max: int

class MapVillage(BaseModel):
    id: str
    name: str
    location: Location
    user_info: UserBasicInfo = Field(..., description="User information containing id, family_name, and color")
    is_owned: bool
    resources: Dict[str, ResourceInfo] = None
    resource_fields: Optional[List[ResourceFieldsInfo]] = None
    city: Optional[CityInfo] = None
    construction_tasks: Optional[List[ConstructionTask]] = Field(default_factory=list, description="List of village's construction tasks")
    base_costs: Optional[Dict[str, Dict[str, Dict[str, int]]]] = Field(
        default=None,
        description="Base costs for creating buildings and resource fields"
    )
    base_creation_times: Optional[Dict[str, Dict[str, int]]] = Field(
        default=None,
        description="Base creation times in minutes for buildings and resource fields"
    )

class MapInfoResponse(BaseModel):
    map_bounds: MapBounds
    map_size: int
    villages: List[MapVillage]
    server_time: str = Field(..., description="Current server time when the request was made")
