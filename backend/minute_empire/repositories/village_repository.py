from typing import List, Optional, Dict, Any
from minute_empire.schemas.schemas import VillageInDB
from minute_empire.domain.village import Village
from minute_empire.db.mongodb import get_db
from bson import ObjectId

class VillageRepository:
    """Repository for accessing and persisting villages"""
    
    COLLECTION = "villages"
    
    async def get_by_id(self, village_id: str) -> Optional[Village]:
        """Get village domain object by ID"""
        async with get_db() as db:
            village_data = await db[self.COLLECTION].find_one({"_id": village_id})
            if village_data is None:
                return None
            
            # Convert DB dict to Pydantic model
            village_model = VillageInDB(**village_data)
            
            # Wrap in domain object
            return Village(village_model)
    
    async def get_by_owner(self, owner_id: str) -> List[Village]:
        """Get all villages owned by a specific user"""
        async with get_db() as db:
            cursor = db[self.COLLECTION].find({"owner_id": owner_id})
            villages_data = await cursor.to_list(length=100)  # Limit to 100 villages per user
            
            # Convert to domain objects
            villages = []
            for village_data in villages_data:
                village_model = VillageInDB(**village_data)
                villages.append(Village(village_model))
                
            return villages
    
    async def get_by_location(self, x: int, y: int) -> Optional[Village]:
        """Get village at specific location"""
        async with get_db() as db:
            village_data = await db[self.COLLECTION].find_one({"location.x": x, "location.y": y})
            if village_data is None:
                return None
            
            # Convert DB dict to Pydantic model
            village_model = VillageInDB(**village_data)
            
            # Wrap in domain object
            return Village(village_model)
    
    async def save(self, village: Village) -> bool:
        """Save changes to a village back to the database"""
        if not village.has_changes():
            return True
            
        # Convert to dict and validate against schema
        try:
            village_dict = village.to_dict()
            # Validate against schema
            VillageInDB(**village_dict)
            
            # Remove the _id field from the update dict
            if "_id" in village_dict:
                village_dict.pop("_id")
                
            async with get_db() as db:
                result = await db[self.COLLECTION].update_one(
                    {"_id": village.id},
                    {"$set": village_dict}
                )
                
                return result.modified_count > 0
        except Exception as e:
            # If validation fails, raise an error
            raise ValueError(f"Invalid village data: {str(e)}")
    
    async def create(self, village_data: Dict[str, Any]) -> Optional[Village]:
        """Create a new village"""
        # Ensure the village has an ID
        if "_id" not in village_data:
            village_data["_id"] = str(ObjectId())
            
        # Validate against schema before inserting
        try:
            VillageInDB(**village_data)
        except Exception as e:
            raise ValueError(f"Invalid village data: {str(e)}")
            
        async with get_db() as db:
            # Insert into database
            await db[self.COLLECTION].insert_one(village_data)
            
            # Return a new Village domain object
            village_model = VillageInDB(**village_data)
            return Village(village_model)
    
    async def delete(self, village_id: str) -> bool:
        """Delete a village"""
        async with get_db() as db:
            result = await db[self.COLLECTION].delete_one({"_id": village_id})
            return result.deleted_count > 0 