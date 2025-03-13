import os
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from dotenv import load_dotenv
import pathlib
from contextlib import asynccontextmanager

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

@asynccontextmanager
async def get_db():
    """Context manager for database connections.
    
    Usage:
        async with get_db() as db:
            result = await db.collection.find_one(...)
    """
    client = AsyncIOMotorClient(MONGODB_URI)
    try:
        db = client[DATABASE_NAME]
        yield db
    finally:
        client.close()