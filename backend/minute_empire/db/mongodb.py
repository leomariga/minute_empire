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