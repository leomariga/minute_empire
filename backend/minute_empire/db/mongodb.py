import os
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from dotenv import load_dotenv
import pathlib

from ..schemas.schemas import (
    UserInDB, 
    VillageInDB, 
    Location, 
    Resources, 
    ResourceField, 
    ResourceFieldType,
    Construction,
    ConstructionType,
    City
)

# Determine the project root directory and path to .env file
project_root = pathlib.Path(__file__).parent.parent.parent.parent  # Go up 4 levels from this file
env_path = project_root / "docker" / ".env"

# Load environment variables from the .env file in the docker directory
load_dotenv(dotenv_path=env_path)

# MongoDB connection settings
MONGO_USER = os.getenv("MONGO_USER")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")
MONGO_DB = os.getenv("MONGO_DB")
DATABASE_NAME = os.getenv("DATABASE_NAME") or MONGO_DB  # Use MONGO_DB as fallback

# Construct MongoDB URI
# Use localhost for direct connections, mongodb for docker-compose connections
host = "mongodb" if os.getenv("DOCKER_ENV") else "localhost"
MONGODB_URI = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{host}:27017/{MONGO_DB}?authSource=admin"

print(f"Connecting to MongoDB at: {host}:27017 with user {MONGO_USER} and database {MONGO_DB}")
print(f"Using database name: {DATABASE_NAME}")

# MongoDB client instance (async)
async_client = None
async_db = None

async def connect_to_mongodb() -> AsyncIOMotorDatabase:
    """Connect to MongoDB asynchronously.
    
    Returns:
        AsyncIOMotorDatabase: MongoDB database instance
    """
    global async_client, async_db
    try:
        async_client = AsyncIOMotorClient(MONGODB_URI)
        async_db = async_client[DATABASE_NAME]
        print(f"Connected to MongoDB at {MONGODB_URI.split('@')[-1] if '@' in MONGODB_URI else MONGODB_URI}")
        return async_db
    except Exception as e:
        print(f"Could not connect to MongoDB: {e}")
        raise

async def close_mongodb_connection() -> None:
    """Close MongoDB connection."""
    global async_client
    if async_client:
        async_client.close()
        print("Closed MongoDB connection")

def get_database() -> AsyncIOMotorDatabase:
    """Return async database instance."""
    return async_db

async def create_user(username: str, password: str, family_name: str, color: str) -> Dict:
    """Create a new user.
    
    Args:
        username: Username (min length 3, max length 50)
        password: Password (min length 8)
        family_name: Family name (min length 2, max length 50)
        color: Hex color code for the user
        
    Returns:
        Dict: Created user data (without password)
    """
    db = await connect_to_mongodb()
    users_collection = db["users"]
    
    # Check if user already exists
    existing_user = await users_collection.find_one({"username": username})
    if existing_user:
        raise ValueError(f"User {username} already exists!")
    
    # Create user document
    now = datetime.utcnow()
    user_in_db = UserInDB(
        _id=str(ObjectId()),
        username=username,
        password=password,
        family_name=family_name,
        color=color,
        created_at=now,
        updated_at=now
    )
    
    # Insert user
    await users_collection.insert_one(user_in_db.dict(by_alias=True))
    print(f"Created user: {username}")
    
    # Return user data without password
    user_dict = user_in_db.dict(by_alias=True)
    user_dict.pop("password")
    return user_dict

async def get_all_users() -> List[Dict]:
    """Get all users.
    
    Returns:
        List[Dict]: List of all users (without passwords)
    """
    db = await connect_to_mongodb()
    users_collection = db["users"]
    
    # Find all users
    cursor = users_collection.find()
    users = await cursor.to_list(length=100)
    
    # Remove passwords from results
    for user in users:
        if "password" in user:
            user.pop("password")
    
    return users

async def initialize_village(owner_id: str, name: str, location: Location) -> VillageInDB:
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
    village_doc = {
        "_id": str(ObjectId()),
        "name": name,
        "location": location.dict(),
        "owner_id": owner_id,
        "resource_fields": [field.dict() for field in initial_fields],
        "resources": Resources().dict(),
        "city": initial_city.dict(),
        "created_at": now,
        "updated_at": now
    }
    
    # Insert village
    await villages_collection.insert_one(village_doc)
    print(f"Created village '{name}' for user {owner_id} at location {location}")
    return VillageInDB(**village_doc) 