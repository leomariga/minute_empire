import logging
from typing import Dict, Any, Set, Optional, List
from fastapi import WebSocket, WebSocketDisconnect
import json

logger = logging.getLogger(__name__)

class WebSocketService:
    """Service for managing WebSocket connections and broadcasting messages"""
    
    def __init__(self):
        # Store active connections by user_id
        self.active_connections: Dict[str, WebSocket] = {}
        # Store user_ids by their village_ids for targeted broadcasts
        self.village_owners: Dict[str, str] = {}
        
    async def connect(self, websocket: WebSocket, user_id: str, village_ids: List[str] = None):
        """Connect a user's websocket and store their village ownership"""
        # The websocket is already accepted in the websocket_endpoint function
        # so we remove the accept() call here
        self.active_connections[user_id] = websocket
        
        # Map each village to its owner for targeted broadcasts
        if village_ids:
            for village_id in village_ids:
                self.village_owners[village_id] = user_id
                
        logger.info(f"User {user_id} connected to WebSocket. Now {len(self.active_connections)} active connections")
        
    async def disconnect(self, user_id: str):
        """Disconnect a user's websocket"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"User {user_id} disconnected from WebSocket. Now {len(self.active_connections)} active connections")
        
    async def broadcast_to_user(self, user_id: str, message: Dict[str, Any]):
        """Broadcast a message to a specific user"""
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            try:
                await websocket.send_text(json.dumps(message))
                logger.debug(f"Broadcast to user {user_id} successful")
                return True
            except Exception as e:
                logger.error(f"Error broadcasting to user {user_id}: {str(e)}")
                return False
        else:
            logger.debug(f"Cannot broadcast to user {user_id} - not connected")
            return False
            
    async def broadcast_to_village_owner(self, village_id: str, message: Dict[str, Any]):
        """Broadcast a message to the owner of a specific village"""
        if village_id in self.village_owners:
            user_id = self.village_owners[village_id]
            return await self.broadcast_to_user(user_id, message)
        else:
            logger.debug(f"Cannot broadcast to village {village_id} - unknown owner")
            return False
            
    async def broadcast_to_all(self, message: Dict[str, Any]):
        """Broadcast a message to all connected users"""
        disconnected_users = []
        for user_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting to user {user_id}: {str(e)}. Will disconnect.")
                disconnected_users.append(user_id)
                
        # Clean up disconnected users
        for user_id in disconnected_users:
            await self.disconnect(user_id)
            
        return len(self.active_connections) - len(disconnected_users)
    
    async def broadcast_map_update(self, user_id: str):
        """
        Broadcast map update to a specific user.
        This is a convenience method that wraps the common pattern of sending map info.
        """
        # Import here to avoid circular imports
        from minute_empire.main import get_map_info_internal
        
        try:
            # Get the map info for this user
            map_info = await get_map_info_internal(user_id)
            
            if not map_info:
                logger.error(f"Failed to get map info for user {user_id}")
                return False
            
            # Create a message with the map info and a type
            message = {
                "type": "map_update",
                "data": map_info
            }
            
            # Broadcast to the user
            success = await self.broadcast_to_user(user_id, message)
            return success
            
        except Exception as e:
            logger.error(f"Error broadcasting map update to user {user_id}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False
            
    async def broadcast_construction_complete(self, village_id: str):
        """
        Broadcast a construction completion event to the village owner.
        """
        if village_id in self.village_owners:
            user_id = self.village_owners[village_id]
            success = await self.broadcast_map_update(user_id)
            if not success:
                logger.warning(f"Failed to broadcast construction completion for village {village_id}")
            return success
        else:
            logger.debug(f"Cannot broadcast construction completion - village {village_id} has no known owner")
            return False
            
    async def broadcast_troop_action_complete(self):
        """
        Broadcast a troop action completion event to all connected users.
        """
        if not self.active_connections:
            logger.debug("No active connections for troop action broadcast")
            return False
        
        # Send map updates to all connected users
        success_count = 0
        for user_id in list(self.active_connections.keys()):  # Use list to avoid modification during iteration
            try:
                if await self.broadcast_map_update(user_id):
                    success_count += 1
            except Exception as e:
                logger.error(f"Error broadcasting troop action to {user_id}: {str(e)}")
            
        return success_count > 0

# Global instance of the websocket service
websocket_service = WebSocketService() 