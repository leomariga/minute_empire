from typing import List, Optional, Dict, Any
from minute_empire.schemas.schemas import TroopInDB, TroopMode
from minute_empire.db.mongodb import get_db
from bson import ObjectId

class TroopsRepository:
    """Repository for accessing and persisting troops"""
    
    COLLECTION = "troops"
    
    async def get_by_id(self, troop_id: str) -> Optional[TroopInDB]:
        """Get troop domain object by ID"""
        async with get_db() as db:
            troop_data = await db[self.COLLECTION].find_one({"_id": troop_id})
            if troop_data is None:
                return None
            
            # Convert DB dict to Pydantic model with error handling
            try:
                return TroopInDB(**troop_data)
            except Exception as e:
                print(f"Error loading troop {troop_id}: {str(e)}")
                return None
    
    async def get_by_home(self, home_id: str) -> List[TroopInDB]:
        """Get all troops belonging to a specific village"""
        async with get_db() as db:
            # Exclude troops with quantity=0 or mode=DEAD
            cursor = db[self.COLLECTION].find({
                "home_id": home_id,
                "quantity": {"$gt": 0},
                "mode": {"$ne": TroopMode.DEAD.value}
            })
            troops_data = await cursor.to_list(length=100)  # Limit to 100 troops per village
            
            # Convert to domain objects with error handling
            valid_troops = []
            for troop_data in troops_data:
                try:
                    valid_troops.append(TroopInDB(**troop_data))
                except Exception as e:
                    print(f"Error converting troop data for home {home_id}: {str(e)}")
                    continue
                    
            return valid_troops
    
    async def save(self, troop: TroopInDB) -> bool:
        """Save changes to a troop back to the database"""
        # Convert to dict and validate against schema
        try:
            troop_dict = troop.dict(by_alias=True)
            # Validate against schema
            TroopInDB(**troop_dict)
            
            # Remove the _id field from the update dict
            if "_id" in troop_dict:
                troop_dict.pop("_id")
                
            async with get_db() as db:
                result = await db[self.COLLECTION].update_one(
                    {"_id": troop.id},
                    {"$set": troop_dict}
                )
                
                return result.modified_count > 0
        except Exception as e:
            # If validation fails, raise an error
            raise ValueError(f"Invalid troop data: {str(e)}")
    
    async def create(self, troop_data: Dict[str, Any]) -> Optional[TroopInDB]:
        """Create a new troop"""
        # Ensure the troop has an ID
        if "_id" not in troop_data:
            troop_data["_id"] = str(ObjectId())
            
        # Validate against schema before inserting
        try:
            TroopInDB(**troop_data)
        except Exception as e:
            raise ValueError(f"Invalid troop data: {str(e)}")
            
        async with get_db() as db:
            # Insert into database
            await db[self.COLLECTION].insert_one(troop_data)
            
            # Return a new Troop domain object
            return TroopInDB(**troop_data)
    
    async def delete(self, troop_id: str) -> bool:
        """Delete a troop"""
        async with get_db() as db:
            result = await db[self.COLLECTION].delete_one({"_id": troop_id})
            return result.deleted_count > 0
    
    async def get_all(self) -> List[TroopInDB]:
        """Get all troops in the game world"""
        async with get_db() as db:
            # Exclude troops with quantity=0 or marked as DEAD
            cursor = db[self.COLLECTION].find({
                "quantity": {"$gt": 0},
                "mode": {"$ne": TroopMode.DEAD.value}
            })
            troops_data = await cursor.to_list(length=1000)  # Limit to 1000 troops
            
            # Convert to domain objects with error handling
            valid_troops = []
            for troop_data in troops_data:
                try:
                    valid_troops.append(TroopInDB(**troop_data))
                except Exception as e:
                    print(f"Error converting troop data: {str(e)}")
                    continue
                    
            return valid_troops
            
    async def update(self, troop_id: str, update_data: Dict[str, Any]) -> bool:
        """Update a troop with the given data"""
        async with get_db() as db:
            result = await db[self.COLLECTION].update_one(
                {"_id": troop_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
    
    async def get_troops_at_location(self, x: int, y: int, exclude_dead: bool = True) -> List[TroopInDB]:
        """Get all troops at a specific location"""
        query = {
            "location.x": x,
            "location.y": y,
            "quantity": {"$gt": 0}  # Only include troops with quantity > 0
        }
        
        if exclude_dead:
            query["mode"] = {"$ne": TroopMode.DEAD.value}
            
        async with get_db() as db:
            cursor = db[self.COLLECTION].find(query)
            troops_data = await cursor.to_list(length=100)  # Limit to 100 troops per location
            
            # Convert to domain objects with error handling
            valid_troops = []
            for troop_data in troops_data:
                try:
                    valid_troops.append(TroopInDB(**troop_data))
                except Exception as e:
                    print(f"Error converting troop data at location ({x},{y}): {str(e)}")
                    continue
                    
            return valid_troops 