import os
import sys
import asyncio
from pprint import pprint
from datetime import datetime
import random
from bson import ObjectId
from typing import Dict

# Import our utility module
from minute_empire.db.mongodb import (
    connect_to_mongodb,
    close_mongodb_connection,
)
from minute_empire.schemas.schemas import (
    UserInDB,
    VillageInDB,
    Location, 
    TroopType, 
    TroopMode, 
    ResourceFieldType,
    ResourceField,
    Construction,
    ConstructionType,
    City
)
from ..core.world import World
from .authentication import get_password_hash

# Get map boundaries statically from World class
x_min, x_max, y_min, y_max = World.get_map_bounds()

async def generate_available_location(max_attempts: int = 100) -> Location:
    """
    Generate a random location for a new village.
    
    Args:
        max_attempts: Maximum number of attempts to find an available location
        
    Returns:
        Location: Available location coordinates
        
    Raises:
        ValueError: If no available location found after max_attempts
    """
    db = await connect_to_mongodb()
    villages_collection = db["villages"]
    
    try:
        for _ in range(max_attempts):
            # Generate random coordinates within map boundaries from World class
            x = random.randint(x_min, x_max)
            y = random.randint(y_min, y_max)
            
            # Check if location is available
            existing_village = await villages_collection.find_one({
                "location.x": x,
                "location.y": y
            })
            
            if not existing_village:
                return Location(x=x, y=y)
        
        # If we reach here, we couldn't find an available location
        raise ValueError(f"Could not find available location after {max_attempts} attempts")
    finally:
        # Ensure the MongoDB connection is closed
        await close_mongodb_connection()

async def create_user_and_village(
    username: str, 
    password: str, 
    family_name: str, 
    color: str, 
    village_name: str
) -> Dict:
    """
    Create a new user and their first village.
    
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
    db = await connect_to_mongodb()
    users_collection = db["users"]
    
    # Check if user already exists
    existing_user = await users_collection.find_one({"username": username})
    if existing_user:
        raise ValueError(f"User {username} already exists!")
    
    # Generate password hash
    hashed_password = get_password_hash(password)
    
    # Create user document
    now = datetime.utcnow()
    user_id = str(ObjectId())
    user_in_db = {
        "_id": user_id,
        "username": username,
        "password": hashed_password,  # Store hashed password
        "family_name": family_name,
        "color": color,
        "created_at": now,
        "updated_at": now
    }
    
    # Generate a random location for the village
    location = await generate_available_location()
    
    # User and village creation should be done in a transaction
    # but MongoDB transactions require a replica set
    # For simplicity, we'll just create them sequentially
    
    user = None
    village = None
    
    try:
        # Insert user
        await users_collection.insert_one(user_in_db)
        print(f"Created user: {username} with ID: {user_id}")
        
        # Create first village
        village = await initialize_village(user_id, village_name, location)
        
        # Return both IDs
        return {
            "user_id": user_id,
            "village_id": village.id
        }
    except Exception as e:
        # If village creation fails, attempt to delete the user
        if user and not village:
            await users_collection.delete_one({"_id": user_id})
        raise e
    finally:
        # Close MongoDB connection
        await close_mongodb_connection()

async def initialize_village(owner_id: str, name: str, location: Location):
    """Create a new village for a user.
    
    Args:
        owner_id: ID of the user who owns the village
        name: Name of the village
        location: Location coordinates for the village
        
    Returns:
        VillageInDB: Created village data
    """
    db = await connect_to_mongodb()
    villages_collection = db["villages"]
    
    try:
        # Check if location is already occupied
        existing_village = await villages_collection.find_one({
            "location.x": location.x,
            "location.y": location.y
        })
        if existing_village:
            raise ValueError(f"Location {location} is already occupied!")
        
        # Create 20 empty resource fields using list comprehension
        initial_fields = [ResourceField(type=ResourceFieldType.EMPTY, level=0) for _ in range(20)]
        
        # Create a City with a wall, a city center, and 24 additional empty construction slots
        initial_city = City(
            wall=Construction(type=ConstructionType.WALL, level=0),
            constructions=[
                Construction(type=ConstructionType.CITY_CENTER, level=0),  # First slot is the city center
                *[Construction(type=ConstructionType.EMPTY, level=0) for _ in range(24)]  # 24 empty slots
            ]
        )
        
        # Create village document
        now = datetime.utcnow()
        village_id = str(ObjectId())
        village_doc = {
            "_id": village_id,
            "name": name,
            "location": location.dict(),
            "owner_id": owner_id,
            "resource_fields": [field.dict() for field in initial_fields],
            "resources": {
                "wood": 500,  # Starting resources
                "stone": 500,
                "iron": 100,
                "food": 1000
            },
            "city": initial_city.dict(),
            "created_at": now,
            "updated_at": now
        }
        
        # Insert village
        await villages_collection.insert_one(village_doc)
        print(f"Created village '{name}' for user {owner_id} at location {location}")
        
        # Return village with its ID
        return VillageInDB(**village_doc)
    finally:
        # Ensure the MongoDB connection is closed
        await close_mongodb_connection()