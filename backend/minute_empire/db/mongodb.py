import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/minute_empire")
DATABASE_NAME = os.getenv("DATABASE_NAME", "minute_empire")

# MongoDB client instance
client = None
db = None

async def connect_to_mongodb():
    """Connect to MongoDB."""
    global client, db
    try:
        client = AsyncIOMotorClient(MONGODB_URI)
        db = client[DATABASE_NAME]
        print(f"Connected to MongoDB at {MONGODB_URI}")
    except Exception as e:
        print(f"Could not connect to MongoDB: {e}")
        raise

async def close_mongodb_connection():
    """Close MongoDB connection."""
    global client
    if client:
        client.close()
        print("Closed MongoDB connection")

def get_database():
    """Return database instance."""
    return db 