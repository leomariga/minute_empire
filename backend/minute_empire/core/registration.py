import os
import sys
import asyncio
from pprint import pprint
from datetime import datetime
import random

# Import our utility module
from minute_empire.db.mongodb import (
    connect_to_mongodb,
    close_mongodb_connection,
    create_user,
    initialize_village,
    get_all_users
)
from minute_empire.schemas.schemas import (
    UserInDB,
    VillageInDB,
    Location, 
    TroopType, 
    TroopMode, 
    ResourceFieldType
)
from ..core.world import World

async def create_user_and_village(username: str, password: str, family_name: str, color: str, village_name: str):
    """
    Create a new user and their first village.
    
    Args:
        username: User's username
        password: User's password
        family_name: User's family name
        color: Hex color code for the user
        village_name: Name for the user's first village
        
    Returns:
        dict: Dictionary containing user_id and village_id
    """
    # Connect to MongoDB
    await connect_to_mongodb()
    
    user = None
    village = None
    
    # Create a test user with a village
    print("\nCreating test user...")
    try:
        # Create the user with individual parameters
        user = await create_user(
            username=username,
            password=password,
            family_name=family_name,
            color=color
        )
        print(f"Created user: {user['username']}")
        pprint(user)
    except ValueError as e:
        print(f"Note: {e}")
        # If user already exists, continue with the test
        raise  # Re-raise the error to be handled by the caller

    if not user:
        raise ValueError(f"Failed to create user {username}")

    # Create a village for the user
    print("\nCreating village for user...")
    try:
        # Get a random available location
        village_location = await generate_available_location()
        village = await initialize_village(
            owner_id=user["_id"],
            name=village_name,
            location=village_location
        )
        print(f"Created village for user {user['username']}:")
        pprint(village.dict(by_alias=True))
    except ValueError as e:
        print(f"Note: {e}")
        # If village already exists at this location, continue
        raise  # Re-raise the error to be handled by the caller

    # Close the connection
    await close_mongodb_connection()
    print("\nMongoDB operations completed successfully")
    
    # Return the required information
    return {
        "user_id": user["_id"],
        "village_id": village.id if village else None
    }

async def generate_available_location(max_attempts=50) -> Location:
    """
    Generate a random location within the map boundaries that is not already occupied.
    
    Args:
        max_attempts: Maximum number of attempts to find an available location
        
    Returns:
        Location: An available location with random coordinates
        
    Raises:
        ValueError: If cannot find an available location after max_attempts
    """
    # Create a World instance to get boundaries
    world = World()
    x_min, x_max, y_min, y_max = world.get_map_bounds()
    
    # Connect to the database to check availability
    db = await connect_to_mongodb()
    villages_collection = db["villages"]
    
    # Try to find an available location
    for _ in range(max_attempts):
        # Generate random coordinates within boundaries
        random_x = random.randint(x_min, x_max)
        random_y = random.randint(y_min, y_max)
        
        # Check if this location is already occupied
        existing_village = await villages_collection.find_one({
            "location.x": random_x,
            "location.y": random_y
        })
        
        # If location is available, return it
        if not existing_village:
            return Location(x=random_x, y=random_y)
    
    # If we get here, we couldn't find an available location
    raise ValueError(f"Could not find an available location after {max_attempts} attempts")