import os
import jwt
from datetime import datetime, timedelta
from typing import Dict, Optional
from fastapi import HTTPException
from passlib.context import CryptContext

from ..db.mongodb import connect_to_mongodb

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-for-development")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 1 week

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)

def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def authenticate_user(username: str, password: str) -> Dict:
    """Authenticate a user with username and password."""
    db = await connect_to_mongodb()
    users_collection = db["users"]
    
    # Find user by username
    user = await users_collection.find_one({"username": username})
    
    if not user:
        raise ValueError("Invalid username or password")
    
    # Verify password
    if not verify_password(password, user["password"]):
        raise ValueError("Invalid username or password")
    
    # Return user without password
    user_dict = dict(user)
    user_dict.pop("password")
    return user_dict

async def get_user_by_id(user_id: str) -> Dict:
    """Get user by ID."""
    db = await connect_to_mongodb()
    users_collection = db["users"]
    
    user = await users_collection.find_one({"_id": user_id})
    if not user:
        raise ValueError("User not found")
    
    # Return user without password
    user_dict = dict(user)
    user_dict.pop("password")
    return user_dict

async def get_user_villages(user_id: str) -> list:
    """Get all villages owned by a user."""
    db = await connect_to_mongodb()
    villages_collection = db["villages"]
    
    cursor = villages_collection.find({"owner_id": user_id})
    villages = await cursor.to_list(length=100)
    
    return villages 