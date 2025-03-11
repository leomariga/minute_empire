import os
from typing import Dict, List, Optional, Any, Union
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import MongoClient
from dotenv import load_dotenv
import pathlib

# Determine the project root directory and path to .env file
project_root = pathlib.Path(__file__).parent.parent.parent.parent  # Go up 4 levels from this file
env_path = project_root / "docker" / ".env"

# Load environment variables from the .env file in the docker directory
load_dotenv(dotenv_path=env_path)

# MongoDB connection settings
MONGO_USER = os.getenv("MONGO_USER")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")
MONGO_DB = os.getenv("MONGO_DB")
DATABASE_NAME = os.getenv("DATABASE_NAME")

# Construct MongoDB URI
# Use localhost for direct connections, mongodb for docker-compose connections
host = "mongodb" if os.getenv("DOCKER_ENV") else "localhost"
MONGODB_URI = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{host}:27017/{MONGO_DB}?authSource=admin"

print(f"Connecting to MongoDB at: {host}:27017 with user {MONGO_USER} and database {MONGO_DB}")

# MongoDB client instance (async)
async_client = None
async_db = None

# MongoDB client instance (sync)
sync_client = None
sync_db = None

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

def get_sync_client() -> MongoClient:
    """Connect to MongoDB synchronously.
    
    Returns:
        MongoClient: MongoDB client instance
    """
    global sync_client, sync_db
    try:
        if not sync_client:
            sync_client = MongoClient(MONGODB_URI)
            # Test the connection
            sync_client.admin.command('ping')
            sync_db = sync_client[DATABASE_NAME]
            print(f"Connected to MongoDB at {MONGODB_URI.split('@')[-1] if '@' in MONGODB_URI else MONGODB_URI}")
        return sync_client
    except Exception as e:
        print(f"Could not connect to MongoDB: {e}")
        raise

def get_sync_database() -> Any:
    """Return sync database instance."""
    global sync_client, sync_db
    if not sync_client:
        get_sync_client()
    return sync_db

def close_sync_connection() -> None:
    """Close synchronous MongoDB connection."""
    global sync_client
    if sync_client:
        sync_client.close()
        print("Closed synchronous MongoDB connection")

# User management utility functions

async def create_user_async(
    username: str, 
    password: str, 
    email: Optional[str] = None, 
    role: str = "user"
) -> str:
    """Create a new user asynchronously.
    
    Args:
        username: Username for the new user
        password: Password for the new user
        email: Email address for the new user
        role: Role for the new user
        
    Returns:
        str: ID of the created user
    """
    from datetime import datetime
    
    db = await connect_to_mongodb()
    users_collection = db["users"]
    
    # Check if user already exists
    existing_user = await users_collection.find_one({"username": username})
    if existing_user:
        print(f"User '{username}' already exists!")
        return str(existing_user["_id"])
    
    # Create user document
    user_doc = {
        "username": username,
        "password": password,  # Should be hashed in production!
        "email": email,
        "role": role,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    # Insert user
    result = await users_collection.insert_one(user_doc)
    print(f"Created user '{username}' with ID: {result.inserted_id}")
    return str(result.inserted_id)

async def get_all_users_async() -> List[Dict[str, Any]]:
    """Get all users asynchronously.
    
    Returns:
        List[Dict[str, Any]]: List of user documents
    """
    db = await connect_to_mongodb()
    users_collection = db["users"]
    
    # Find all users, excluding passwords
    cursor = users_collection.find({}, {"password": 0})
    users = await cursor.to_list(length=100)
    print(f"Found {len(users)} users")
    return users

def create_user_sync(
    username: str, 
    password: str, 
    email: Optional[str] = None, 
    role: str = "user"
) -> str:
    """Create a new user synchronously.
    
    Args:
        username: Username for the new user
        password: Password for the new user
        email: Email address for the new user
        role: Role for the new user
        
    Returns:
        str: ID of the created user
    """
    from datetime import datetime
    
    db = get_sync_database()
    users_collection = db["users"]
    
    # Check if user already exists
    existing_user = users_collection.find_one({"username": username})
    if existing_user:
        print(f"User '{username}' already exists!")
        return str(existing_user["_id"])
    
    # Create user document
    user_doc = {
        "username": username,
        "password": password,  # Should be hashed in production!
        "email": email,
        "role": role,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    # Insert user
    result = users_collection.insert_one(user_doc)
    print(f"Created user '{username}' with ID: {result.inserted_id}")
    return str(result.inserted_id)

def get_all_users_sync() -> List[Dict[str, Any]]:
    """Get all users synchronously.
    
    Returns:
        List[Dict[str, Any]]: List of user documents
    """
    db = get_sync_database()
    users_collection = db["users"]
    
    # Find all users, excluding passwords
    users = list(users_collection.find({}, {"password": 0}))
    print(f"Found {len(users)} users")
    return users 