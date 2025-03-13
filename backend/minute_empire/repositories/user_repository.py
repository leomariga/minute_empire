from typing import List, Optional, Dict, Any
from minute_empire.schemas.schemas import UserInDB
from minute_empire.domain.user import User
from minute_empire.db.mongodb import get_db
from bson import ObjectId

class UserRepository:
    """Repository for accessing and persisting users"""
    
    COLLECTION = "users"
    
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user domain object by ID"""
        async with get_db() as db:
            user_data = await db[self.COLLECTION].find_one({"_id": user_id})
            if user_data is None:
                return None
            
            # Convert DB dict to Pydantic model
            user_model = UserInDB(**user_data)
            
            # Wrap in domain object
            return User(user_model)
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user domain object by username"""
        async with get_db() as db:
            user_data = await db[self.COLLECTION].find_one({"username": username})
            if user_data is None:
                return None
            
            # Convert DB dict to Pydantic model
            user_model = UserInDB(**user_data)
            
            # Wrap in domain object
            return User(user_model)
    
    async def get_all(self, limit: int = 100, skip: int = 0) -> List[User]:
        """Get all users with pagination"""
        async with get_db() as db:
            cursor = db[self.COLLECTION].find().skip(skip).limit(limit)
            users_data = await cursor.to_list(length=limit)
            
            # Convert to domain objects
            users = []
            for user_data in users_data:
                user_model = UserInDB(**user_data)
                users.append(User(user_model))
                
            return users
    
    async def save(self, user: User) -> bool:
        """Save changes to a user back to the database"""
        if not user.has_changes():
            return True
            
        # Convert to dict and validate against schema
        try:
            user_dict = user.to_dict(include_password=True)
            # Validate against schema
            UserInDB(**user_dict)
            
            # Remove the _id field from the update dict
            if "_id" in user_dict:
                user_dict.pop("_id")
                
            async with get_db() as db:
                result = await db[self.COLLECTION].update_one(
                    {"_id": user.id},
                    {"$set": user_dict}
                )
                
                return result.modified_count > 0
        except Exception as e:
            # If validation fails, raise an error
            raise ValueError(f"Invalid user data: {str(e)}")
    
    async def create(self, user_data: Dict[str, Any]) -> Optional[User]:
        """Create a new user"""
        async with get_db() as db:
            # Check if username already exists
            existing_user = await db[self.COLLECTION].find_one({"username": user_data.get("username")})
            if existing_user is not None:
                return None
                
            # Ensure the user has an ID
            if "_id" not in user_data:
                user_data["_id"] = str(ObjectId())
                
            # Validate against schema before inserting
            try:
                UserInDB(**user_data)
            except Exception as e:
                raise ValueError(f"Invalid user data: {str(e)}")
                
            # Insert into database
            await db[self.COLLECTION].insert_one(user_data)
            
            # Return a new User domain object
            user_model = UserInDB(**user_data)
            return User(user_model)
    
    async def delete(self, user_id: str) -> bool:
        """Delete a user"""
        async with get_db() as db:
            result = await db[self.COLLECTION].delete_one({"_id": user_id})
            return result.deleted_count > 0 