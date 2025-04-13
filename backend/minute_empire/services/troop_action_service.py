from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from bson import ObjectId
from minute_empire.repositories.village_repository import VillageRepository
from minute_empire.repositories.troops_repository import TroopsRepository
from minute_empire.repositories.troop_action_repository import TroopActionRepository
from minute_empire.schemas.schemas import ActionType, TroopType, TroopMode, Location
from minute_empire.domain.troop import Troop

class TroopActionService:
    """Service for managing troop actions like movement and combat"""
    
    def __init__(self):
        self.village_repository = VillageRepository()
        self.troops_repository = TroopsRepository()
        self.action_repository = TroopActionRepository()
    
    async def is_troop_available(self, troop_id: str) -> Dict[str, Any]:
        """Check if a troop is available for a new action"""
        # First check if troop exists and is in idle mode
        troop = await self.troops_repository.get_by_id(troop_id)
        if not troop:
            return {"available": False, "reason": f"Troop {troop_id} not found"}
        
        if troop.mode != TroopMode.IDLE:
            return {"available": False, "reason": f"Troop {troop_id} is currently in {troop.mode.value} mode"}
        
        # Then check if there are any active actions for this troop
        active_actions = await self.action_repository.get_active_actions_for_troop(troop_id)
        if len(active_actions) > 0:
            return {"available": False, "reason": f"Troop {troop_id} has {len(active_actions)} active actions"}
            
        return {"available": True}
    
    async def is_valid_move_location(self, troop_id: str, target_x: int, target_y: int) -> Dict[str, Any]:
        """Check if the target location is a valid move location for the troop"""
        troop = await self.troops_repository.get_by_id(troop_id)
        if not troop:
            return {"valid": False, "reason": f"Troop {troop_id} not found"}
        
        # Check if target is within map bounds
        from minute_empire.domain.world import World
        x_min, x_max, y_min, y_max = World.get_map_bounds()
        if target_x < x_min or target_x > x_max or target_y < y_min or target_y > y_max:
            return {"valid": False, "reason": f"Target location ({target_x}, {target_y}) is outside map bounds {x_min}-{x_max}, {y_min}-{y_max}"}
        
        # Calculate Manhattan distance
        distance = abs(target_x - troop.location.x) + abs(target_y - troop.location.y)
        
        if distance == 0:
            return {"valid": False, "reason": f"Troop is already at location ({target_x}, {target_y})"}
            
        # Check if target is within movement range
        max_distance = 100  # Example maximum move distance
        if distance > max_distance:
            return {"valid": False, "reason": f"Target location ({target_x}, {target_y}) is too far. Maximum distance: {max_distance}, actual distance: {distance}"}
        
        return {"valid": True}
    
    async def is_valid_attack_location(self, troop_id: str, target_x: int, target_y: int) -> Dict[str, Any]:
        """Check if the target location is a valid attack location for the troop"""
        troop = await self.troops_repository.get_by_id(troop_id)
        if not troop:
            return {"valid": False, "reason": f"Troop {troop_id} not found"}
        
        # Check map bounds
        from minute_empire.domain.world import World
        x_min, x_max, y_min, y_max = World.get_map_bounds()
        if target_x < x_min or target_x > x_max or target_y < y_min or target_y > y_max:
            return {"valid": False, "reason": f"Target location ({target_x}, {target_y}) is outside map bounds {x_min}-{x_max}, {y_min}-{y_max}"}
        
        # Find village at target location - REMOVED (will be handled during action completion)
        # target_village = await self.village_repository.find_by_location(x=target_x, y=target_y)
        # if not target_village:
        #    return {"valid": False, "reason": f"No village found at location ({target_x}, {target_y})"}
        
        # Don't allow attacking own villages - REMOVED (will be handled during action completion)
        # if troop.home_id == target_village.id:
        #    return {"valid": False, "reason": f"Cannot attack your own village at ({target_x}, {target_y})"}
        
        # Calculate attack range (Manhattan distance)
        distance = abs(target_x - troop.location.x) + abs(target_y - troop.location.y)
        
        # Check if target is within attack range
        max_distance = 100
        if distance > max_distance:
            return {"valid": False, "reason": f"Target location ({target_x}, {target_y}) is too far. Maximum attack range: {max_distance}, actual distance: {distance}"}
        
        # Check if troop is at the same location
        if distance == 0:
            return {"valid": False, "reason": f"Cannot attack the same location where troop is positioned ({target_x}, {target_y})"}
        
        return {"valid": True}
    
    async def verify_troop_ownership(self, troop_id: str, village_id: str) -> Dict[str, Any]:
        """Verify that the troop belongs to the user's village"""
        troop = await self.troops_repository.get_by_id(troop_id)
        if not troop:
            return {"owned": False, "reason": f"Troop {troop_id} not found"}
        
        # Check if the troop's home village matches the requesting village
        if troop.home_id != village_id:
            return {"owned": False, "reason": f"Troop {troop_id} belongs to village {troop.home_id}, not {village_id}"}
            
        return {"owned": True}
    
    async def start_move_action(self, troop_id: str, target_x: int, target_y: int, village_id: str) -> Dict[str, Any]:
        """Start a troop movement action"""
        # First verify ownership
        ownership_check = await self.verify_troop_ownership(troop_id, village_id)
        if not ownership_check["owned"]:
            return {"success": False, "error": ownership_check["reason"]}
        
        # Continue with existing checks
        availability_check = await self.is_troop_available(troop_id)
        if not availability_check["available"]:
            return {"success": False, "error": availability_check["reason"]}
        
        # Check if target location is valid
        location_check = await self.is_valid_move_location(troop_id, target_x, target_y)
        if not location_check["valid"]:
            return {"success": False, "error": location_check["reason"]}
        
        # Get troop details
        troop = await self.troops_repository.get_by_id(troop_id)
        
        # Calculate movement time based on distance
        distance = abs(target_x - troop.location.x) + abs(target_y - troop.location.y)
        # 1 minute per tile is a reasonable starting point
        movement_time_minutes = distance
        
        # Create action data
        action_data = {
            "troop_id": troop_id,
            "action_type": ActionType.MOVE,
            "start_location": {
                "x": troop.location.x,
                "y": troop.location.y
            },
            "target_location": {
                "x": target_x,
                "y": target_y
            },
            "started_at": datetime.utcnow(),
            "completion_time": datetime.utcnow() + timedelta(minutes=movement_time_minutes),
            "processed": False
        }
        
        # Create the action in the database
        try:
            action = await self.action_repository.create(action_data)
            if not action:
                return {"success": False, "error": "Failed to create movement action in database"}
                
            # Update troop status to moving
            update_result = await self.troops_repository.update(troop_id, {"mode": TroopMode.MOVE})
            if not update_result:
                return {"success": False, "error": f"Failed to update troop status to {TroopMode.MOVE}"}
            
            return {
                "success": True,
                "action_id": action.id,
                "message": f"Troop {troop_id} is moving to ({target_x}, {target_y})",
                "estimated_completion": action.completion_time
            }
        except Exception as e:
            return {"success": False, "error": f"Error creating movement action: {str(e)}"}
    
    async def start_attack_action(self, troop_id: str, target_x: int, target_y: int, village_id: str) -> Dict[str, Any]:
        """Start a troop attack action"""
        # First verify ownership
        ownership_check = await self.verify_troop_ownership(troop_id, village_id)
        if not ownership_check["owned"]:
            return {"success": False, "error": ownership_check["reason"]}
        
        # Continue with existing checks
        availability_check = await self.is_troop_available(troop_id)
        if not availability_check["available"]:
            return {"success": False, "error": availability_check["reason"]}
        
        # Check if target location is valid
        location_check = await self.is_valid_attack_location(troop_id, target_x, target_y)
        if not location_check["valid"]:
            return {"success": False, "error": location_check["reason"]}
        
        # Get troop details
        troop = await self.troops_repository.get_by_id(troop_id)
        
        # Calculate attack time based on distance
        distance = abs(target_x - troop.location.x) + abs(target_y - troop.location.y)
        # Attack takes longer than movement
        attack_time_minutes = distance * 2
        
        # Create action data
        action_data = {
            "troop_id": troop_id,
            "action_type": ActionType.ATTACK,
            "start_location": {
                "x": troop.location.x,
                "y": troop.location.y
            },
            "target_location": {
                "x": target_x,
                "y": target_y
            },
            "started_at": datetime.utcnow(),
            "completion_time": datetime.utcnow() + timedelta(minutes=attack_time_minutes),
            "processed": False
        }
        
        # Create the action in the database
        try:
            action = await self.action_repository.create(action_data)
            if not action:
                return {"success": False, "error": "Failed to create attack action in database"}
                
            # Update troop status to attacking
            update_result = await self.troops_repository.update(troop_id, {"mode": TroopMode.ATTACK})
            if not update_result:
                return {"success": False, "error": f"Failed to update troop status to {TroopMode.ATTACK}"}
            
            return {
                "success": True,
                "action_id": action.id,
                "message": f"Troop {troop_id} is attacking location ({target_x}, {target_y})",
                "estimated_completion": action.completion_time
            }
        except Exception as e:
            return {"success": False, "error": f"Error creating attack action: {str(e)}"}
    
    async def process_pending_troop_actions(self) -> Dict[str, Any]:
        """
        Process all troop actions that have reached their completion time.
        This includes movement and attack actions.
        
        Returns:
            Dict[str, Any]: Summary of processed actions
        """
        # Get all pending (unprocessed) actions where completion_time <= now
        pending_actions = await self.action_repository.get_pending_actions()
        
        if not pending_actions:
            return {"success": True, "processed_count": 0, "message": "No pending troop actions found"}
        
        # Debug print - number of pending actions found
        print(f"[TroopActionService] Found {len(pending_actions)} pending troop actions to process")
        
        processed_count = 0
        processed_moves = 0
        processed_attacks = 0
        errors = []
        
        # Process each pending action
        for action in pending_actions:
            try:
                # Get the troop associated with this action
                troop = await self.troops_repository.get_by_id(action.troop_id)
                if not troop:
                    errors.append(f"Troop {action.troop_id} not found for action {action.id}")
                    continue
                
                # Process based on action type
                if action.action_type == ActionType.MOVE:
                    # Update troop location to target location
                    update_data = {
                        "location": {
                            "x": action.target_location.x,
                            "y": action.target_location.y
                        },
                        "mode": TroopMode.IDLE.value
                    }
                    
                    update_result = await self.troops_repository.update(troop.id, update_data)
                    if update_result:
                        processed_moves += 1
                        print(f"[TroopActionService] MOVE completed: Troop {troop.id} moved from ({action.start_location.x},{action.start_location.y}) to ({action.target_location.x},{action.target_location.y})")
                    else:
                        errors.append(f"Failed to update troop {troop.id} location for move action")
                
                elif action.action_type == ActionType.ATTACK:
                    # For now, just update location like a move action
                    # In the future, this will involve combat calculations
                    update_data = {
                        "location": {
                            "x": action.target_location.x,
                            "y": action.target_location.y
                        },
                        "mode": TroopMode.IDLE.value
                    }
                    
                    update_result = await self.troops_repository.update(troop.id, update_data)
                    if update_result:
                        processed_attacks += 1
                        print(f"[TroopActionService] ATTACK completed: Troop {troop.id} attacked at ({action.target_location.x},{action.target_location.y})")
                    else:
                        errors.append(f"Failed to update troop {troop.id} location for attack action")
                
                # Mark action as processed regardless of type
                await self.action_repository.mark_processed(action.id)
                processed_count += 1
                
            except Exception as e:
                errors.append(f"Error processing action {action.id}: {str(e)}")
                print(f"[TroopActionService] Error processing action {action.id}: {str(e)}")
        
        if processed_count > 0:
            print(f"[TroopActionService] Processed {processed_count} troop actions: {processed_moves} moves, {processed_attacks} attacks")
        
        return {
            "success": True,
            "processed_count": processed_count,
            "processed_moves": processed_moves,
            "processed_attacks": processed_attacks,
            "errors": errors,
            "message": f"Processed {processed_count} troop actions ({processed_moves} moves, {processed_attacks} attacks)"
        } 