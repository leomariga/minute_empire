from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from minute_empire.db.mongodb import get_db
from minute_empire.schemas.schemas import TroopActionTaskInDB, ActionType

class TroopActionRepository:
    """Repository for troop action tasks"""
    
    COLLECTION = "troop_actions"
    
    async def create(self, action_data: Dict[str, Any]) -> Optional[TroopActionTaskInDB]:
        """Create a new troop action task"""
        if "_id" not in action_data:
            action_data["_id"] = str(ObjectId())
        
        async with get_db() as db:
            result = await db[self.COLLECTION].insert_one(action_data)
            if result.inserted_id:
                return await self.get_by_id(action_data["_id"])
            return None
    
    async def get_by_id(self, action_id: str) -> Optional[TroopActionTaskInDB]:
        """Get a troop action task by ID"""
        async with get_db() as db:
            action_data = await db[self.COLLECTION].find_one({"_id": action_id})
            if action_data:
                return TroopActionTaskInDB(**action_data)
            return None
    
    async def get_pending_actions(self) -> List[TroopActionTaskInDB]:
        """Get all pending troop action tasks"""
        async with get_db() as db:
            cursor = db[self.COLLECTION].find({
                "processed": False,
                "completion_time": {"$lte": datetime.utcnow()}
            })
            pending_actions = []
            async for doc in cursor:
                pending_actions.append(TroopActionTaskInDB(**doc))
            return pending_actions
    
    async def get_active_actions_for_troop(self, troop_id: str) -> List[TroopActionTaskInDB]:
        """Get all active (non-processed) actions for a troop"""
        async with get_db() as db:
            cursor = db[self.COLLECTION].find({
                "troop_id": troop_id,
                "processed": False
            })
            active_actions = []
            async for doc in cursor:
                active_actions.append(TroopActionTaskInDB(**doc))
            return active_actions
    
    async def update(self, action_id: str, update_data: Dict[str, Any]) -> bool:
        """Update a troop action task"""
        async with get_db() as db:
            result = await db[self.COLLECTION].update_one(
                {"_id": action_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
    
    async def mark_processed(self, action_id: str) -> bool:
        """Mark a troop action task as processed"""
        return await self.update(action_id, {"processed": True})
    
    async def get_all_active(self) -> List[TroopActionTaskInDB]:
        """Get all active (non-processed) actions"""
        async with get_db() as db:
            cursor = db[self.COLLECTION].find({"processed": False})
            active_actions = []
            async for doc in cursor:
                active_actions.append(TroopActionTaskInDB(**doc))
            return active_actions 