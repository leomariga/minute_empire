from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum

class TroopType(str, Enum):
    MILITIA = "militia"
    ARCHER = "archer"
    CAVALRY = "cavalry"
    SPEARMAN = "spearman"

class ResourceFieldType(str, Enum):
    WOOD = "wood"
    STONE = "stone"
    IRON = "iron"
    FOOD = "food"

class TroopMode(str, Enum):
    IDLE = "idle"
    ATTACK = "attack"
    DEFEND = "defend"
    MOVE = "move"

class ConstructionType(str, Enum):
    CITY_CENTER = "city_center"
    RALLY_POINT = "rally_point"
    BARRAKS = "barraks"
    ARCHERY = "archery"
    STABLE = "stable"
    WAREHOUSE = "warehouse"
    GRANARY = "granary"
    HIDE_SPOT = "hide_spot"
    WALL = "wall"

class TaskType(str, Enum):
    CREATE_BUILDING = "create_building"
    UPGRADE_BUILDING = "upgrade_building"
    CREATE_FIELD = "create_field"
    UPGRADE_FIELD = "upgrade_field"

class Construction(BaseModel):
    type: ConstructionType
    level: int = Field(default=0, ge=0)
    slot: int = Field(default=0, ge=0)

class ConstructionTask(BaseModel):
    id: str
    task_type: TaskType
    target_type: str
    slot: int
    level: int = Field(default=1)
    started_at: datetime
    completion_time: datetime
    processed: bool = Field(default=False)

class City(BaseModel):
    wall: Construction = Field(default=Construction(type=ConstructionType.WALL, level=0))
    constructions: List[Construction] = Field(default_factory=list)

class Location(BaseModel):
    x: int = Field(..., description="X coordinate on the map")
    y: int = Field(..., description="Y coordinate on the map")

class Resources(BaseModel):
    wood: float = Field(default=0, ge=0)
    stone: float = Field(default=0, ge=0)
    iron: float = Field(default=0, ge=0)
    food: float = Field(default=0, ge=0)

class ResourceField(BaseModel):
    type: ResourceFieldType
    level: int = Field(default=0, ge=0)
    slot: int = Field(default=0, ge=0)

class UserInDB(BaseModel):
    """Schema for user as stored in database."""
    id: str = Field(alias="_id")
    password: str = Field(..., min_length=8)
    username: str = Field(..., min_length=3, max_length=50)
    family_name: str = Field(..., min_length=2, max_length=50)
    color: str = Field(..., pattern="^#[0-9a-fA-F]{6}$")  # Hex color code
    created_at: datetime
    updated_at: datetime

    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class VillageInDB(BaseModel):
    """Schema for village as stored in database."""
    id: str = Field(alias="_id")
    name: str = Field(..., min_length=3, max_length=50)
    location: Location
    owner_id: str
    resource_fields: List[ResourceField] = Field(default_factory=list)
    resources: Resources = Field(default_factory=Resources)
    city: City = Field(default_factory=City)
    res_update_at: datetime
    created_at: datetime
    updated_at: datetime
    construction_tasks: List[ConstructionTask] = Field(default_factory=list)

    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class TroopInDB(BaseModel):
    """Schema for troop as stored in database."""
    id: str = Field(alias="_id")
    type: TroopType
    mode: TroopMode = Field(default=TroopMode.IDLE)
    home_id: str  # Reference to village ID
    quantity: int = Field(..., gt=0)
    location: Location
    backpack: Resources = Field(default_factory=Resources)  # Resources being carried
    created_at: datetime
    updated_at: datetime

    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        } 