from pydantic import BaseModel, Field, validator
import re

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

# Village models
class VillageResponse(BaseModel):
    id: str
    name: str
    location: dict
    owner_id: str
    resources: dict
    city: dict
    created_at: str

# Command models
class CommandRequest(BaseModel):
    command: str = Field(..., description="Command string to execute")
    village_id: str = Field(..., description="ID of the village to execute the command on")

class CommandResponse(BaseModel):
    success: bool
    message: str
    data: dict = {}
