import jwt
from datetime import datetime, timedelta
from typing import Dict, Optional
from passlib.context import CryptContext
import os

from minute_empire.repositories.user_repository import UserRepository
from minute_empire.domain.user import User

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-for-development")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 1 week

class AuthenticationService:
    """Service for authentication-related operations"""
    
    def __init__(self):
        self.user_repository = UserRepository()
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Generate password hash."""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    async def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate a user with username and password."""
        # Use repository to get the user
        user = await self.user_repository.get_by_username(username)
        
        if not user:
            return None
        
        # Get the password hash from the internal data model
        hashed_password = user._data.password
        
        # Verify password
        if not self.verify_password(password, hashed_password):
            return None
        
        # Return user public info
        return user.get_public_info()
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by ID."""
        # Use repository to get the user
        user = await self.user_repository.get_by_id(user_id)
        
        if not user:
            return None
            
        # Return user public info
        return user.get_public_info() 