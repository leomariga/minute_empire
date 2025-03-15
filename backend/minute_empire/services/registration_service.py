from datetime import datetime
from typing import Dict, Optional
from bson import ObjectId
import random

from minute_empire.repositories.user_repository import UserRepository
from minute_empire.repositories.village_repository import VillageRepository
from minute_empire.domain.world import World
from minute_empire.schemas.schemas import (
    UserInDB,
    VillageInDB,
    Location,
    ResourceFieldType,
    ResourceField,
    Construction,
    ConstructionType,
    City
)
from minute_empire.services.authentication_service import AuthenticationService

class RegistrationService:
    """Service for handling user and village registration"""
    
    def __init__(self):
        self.user_repository = UserRepository()
        self.village_repository = VillageRepository()
        self.auth_service = AuthenticationService()
    
    async def _generate_available_location(self, max_attempts: int = 100) -> Location:
        """Generate a random location for a new village."""
        # Get map boundaries from World class
        x_min, x_max, y_min, y_max = World.get_map_bounds()
        
        for _ in range(max_attempts):
            # Generate random coordinates
            x = random.randint(x_min, x_max)
            y = random.randint(y_min, y_max)
            
            # Check if location is available
            existing_village = await self.village_repository.get_by_location(x, y)
            if existing_village is None:
                return Location(x=x, y=y)
        
        raise ValueError(f"Could not find available location after {max_attempts} attempts")
    
    async def _initialize_village(self, owner_id: str, name: str, location: Location) -> VillageInDB:
        """Create a new village with initial setup."""
        # Create initial resource fields
        initial_fields = []
        
        # Create initial city setup
        initial_city = City(
            wall=Construction(type=ConstructionType.WALL, level=1, slot=0),
            constructions=[
                Construction(type=ConstructionType.CITY_CENTER, level=1, slot=1),
            ]
        )
        
        # Create village data
        now = datetime.utcnow()
        village_data = {
            "_id": str(ObjectId()),
            "name": name,
            "location": location.dict(),
            "owner_id": owner_id,
            "resource_fields": [field.dict() for field in initial_fields],
            "resources": {
                "wood": 0,
                "stone": 0,
                "iron": 0,
                "food": 0
            },
            "city": initial_city.dict(),
            "res_update_at": now,
            "created_at": now,
            "updated_at": now
        }
        
        # Create village using repository
        village = await self.village_repository.create(village_data)
        if village is None:
            raise ValueError(f"Failed to create village at location {location}")
            
        return village
    
    async def register_user_and_village(
        self,
        username: str,
        password: str,
        family_name: str,
        color: str,
        village_name: str
    ) -> Dict:
        """
        Register a new user and create their first village.
        
        Args:
            username: Username (min length 3, max length 50)
            password: Password (min length 8)
            family_name: Family name (min length 2, max length 50)
            color: Hex color code for the user
            village_name: Name of the first village (min length 3, max length 50)
            
        Returns:
            Dict: Dictionary containing user_id and village_id
            
        Raises:
            ValueError: If user already exists or location is occupied
        """
        user = None
        village = None
        
        try:
            # Check if user exists
            existing_user = await self.user_repository.get_by_username(username)
            if existing_user is not None:
                raise ValueError(f"User {username} already exists!")
            
            # Generate password hash
            hashed_password = self.auth_service.get_password_hash(password)
            
            # Create user data
            now = datetime.utcnow()
            user_data = {
                "_id": str(ObjectId()),
                "username": username,
                "password": hashed_password,
                "family_name": family_name,
                "color": color,
                "created_at": now,
                "updated_at": now
            }
            
            # Create user using repository
            user = await self.user_repository.create(user_data)
            if user is None:
                raise ValueError("Failed to create user")
            
            # Generate village location
            location = await self._generate_available_location()
            
            # Create village
            village = await self._initialize_village(user.id, village_name, location)
            if village is None:
                raise ValueError("Failed to create village")
            
            return {
                "user_id": user.id,
                "village_id": village.id
            }
            
        except Exception as e:
            # If anything fails, attempt to clean up
            if user is not None and village is None:
                await self.user_repository.delete(user.id)
            raise e 