from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from bson import ObjectId
from statistics import median
import asyncio
import logging
from minute_empire.repositories.village_repository import VillageRepository
from minute_empire.repositories.troops_repository import TroopsRepository
from minute_empire.repositories.troop_action_repository import TroopActionRepository
from minute_empire.schemas.schemas import ActionType, TroopType, TroopMode, Location, VillageInDB
from minute_empire.domain.troop import Troop
from minute_empire.services.task_scheduler import task_scheduler
from minute_empire.services.websocket_service import websocket_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        
        # Check if target is the same as current location
        if target_x == troop.location.x and target_y == troop.location.y:
            return {"valid": False, "reason": f"Troop is already at location ({target_x}, {target_y})"}
        
        # Get valid move locations for this troop type
        valid_move_spots = Troop.get_valid_move_spots(troop.type, troop.location)
        
        # Check if target location is in valid move spots
        if {"x": target_x, "y": target_y} not in valid_move_spots:
            return {"valid": False, "reason": f"Target location ({target_x}, {target_y}) is not a valid move for {troop.type.value}"}
        
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
        
        # Get valid attack locations for this troop type
        valid_attack_spots = Troop.get_valid_attack_spots(troop.type, troop.location)
        
        # Check if target location is in valid attack spots
        if {"x": target_x, "y": target_y} not in valid_attack_spots:
            return {"valid": False, "reason": f"Target location ({target_x}, {target_y}) is not a valid attack for {troop.type.value}"}
        
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
        movement_time_minutes = 0.2#distance
        
        # Calculate completion time
        now = datetime.utcnow()
        completion_time = now + timedelta(minutes=movement_time_minutes)
        
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
            "started_at": now,
            "completion_time": completion_time,
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
            
            # Schedule the action to be completed at the completion time
            await task_scheduler.schedule_task(
                task_id=action.id,
                execution_time=completion_time,
                callback=self.complete_troop_action,
                action_id=action.id,
                completion_time=completion_time
            )
            
            logger.info(f"Scheduled troop movement: Troop {troop_id} from ({troop.location.x}, {troop.location.y}) to ({target_x}, {target_y}) - completion at {completion_time}")
            
            # Broadcast to all connected users via WebSocket
            await websocket_service.broadcast_troop_action_complete()
            
            return {
                "success": True,
                "action_id": action.id,
                "message": f"Troop {troop_id} is moving to ({target_x}, {target_y})",
                "estimated_completion": completion_time
            }
        except Exception as e:
            logger.error(f"Error creating movement action: {str(e)}")
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
        
        # Calculate completion time
        now = datetime.utcnow()
        completion_time = now + timedelta(minutes=attack_time_minutes)
        
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
            "started_at": now,
            "completion_time": completion_time,
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
            
            # Schedule the action to be completed at the completion time
            await task_scheduler.schedule_task(
                task_id=action.id,
                execution_time=completion_time,
                callback=self.complete_troop_action,
                action_id=action.id,
                completion_time=completion_time
            )
            
            logger.info(f"Scheduled troop attack: Troop {troop_id} from ({troop.location.x}, {troop.location.y}) attacking ({target_x}, {target_y}) - completion at {completion_time}")
            
            # Broadcast to all connected users via WebSocket
            await websocket_service.broadcast_troop_action_complete()
            
            return {
                "success": True,
                "action_id": action.id,
                "message": f"Troop {troop_id} is attacking location ({target_x}, {target_y})",
                "estimated_completion": completion_time
            }
        except Exception as e:
            logger.error(f"Error creating attack action: {str(e)}")
            return {"success": False, "error": f"Error creating attack action: {str(e)}"}
    
    async def complete_troop_action(self, action_id: str, completion_time: datetime) -> Dict[str, Any]:
        """
        Complete a troop action at its scheduled time.
        This is called by the task scheduler when the action's completion time is reached.
        
        Args:
            action_id: The ID of the action to complete
            completion_time: The scheduled completion time of the action
            
        Returns:
            Dict[str, Any]: Result of the operation
        """
        try:
            # Get the action
            action = await self.action_repository.get_by_id(action_id)
            if not action:
                logger.error(f"Action {action_id} not found for completion")
                return {"success": False, "error": "Action not found"}
                
            # Get the troop
            troop = await self.troops_repository.get_by_id(action.troop_id)
            if not troop:
                logger.error(f"Troop {action.troop_id} not found for action {action_id}")
                await self.action_repository.mark_processed(action_id)
                return {"success": False, "error": "Troop not found"}
            
            logger.info(f"Completing action {action_id} for troop {troop.id}: {action.action_type.value} to ({action.target_location.x}, {action.target_location.y})")
            
            # Initialize a list to track villages that need resource updates
            involved_villages = set()
            
            # Add attacker's home village to the list
            involved_villages.add(troop.home_id)
            
            # IMPORTANT: Update resources for all involved villages before processing the action
            # This is necessary for future features like changing food consumption when troops die
            # or resources being affected by combat
            
            # Process based on action type
            result = {"success": True, "message": "Action completed successfully"}
            
            if action.action_type == ActionType.MOVE:
                # Check if there are enemy troops at the target location
                enemy_troops = await self._get_enemy_troops_at_location(
                    troop.home_id, action.target_location.x, action.target_location.y
                )
                
                # Add home villages of all enemy troops to the involved villages
                for enemy_troop in enemy_troops:
                    involved_villages.add(enemy_troop.home_id)
                
                # Check if there's a village at the target location
                target_village = await self.village_repository.find_by_location(
                    action.target_location.x, action.target_location.y
                )
                if target_village:
                    involved_villages.add(target_village.id)
                
                # Update resources for all involved villages before combat
                await self._update_all_village_resources(involved_villages, completion_time)
                
                if enemy_troops:
                    # Combat occurs when moving to a location with enemy troops
                    combat_result = await self._process_combat(
                        attacker_troop=troop,
                        defender_troops=enemy_troops,
                        target_location=action.target_location,
                        is_movement=True,
                        start_location=action.start_location
                    )
                    
                    # If the attacker lost all troops or didn't defeat all defenders, don't move
                    if combat_result["attacker_all_dead"] or not combat_result["all_defenders_defeated"]:
                        # Don't move, update only mode if alive
                        if not combat_result["attacker_all_dead"]:
                            await self.troops_repository.update(troop.id, {"mode": TroopMode.IDLE.value})
                    else:
                        # Attacker won, can move to the location
                        update_data = {
                            "location": {
                                "x": action.target_location.x,
                                "y": action.target_location.y
                            },
                            "mode": TroopMode.IDLE.value
                        }
                        update_result = await self.troops_repository.update(troop.id, update_data)
                        if update_result:
                            logger.info(f"Moved troop {troop.id} to ({action.target_location.x}, {action.target_location.y}) after combat")
                        else:
                            logger.error(f"Failed to update troop {troop.id} location after combat")
                            
                    result["combat"] = combat_result
                    
                    # Add stolen resources to result if any
                    if "stolen_resources" in combat_result:
                        result["stolen_resources"] = combat_result["stolen_resources"]
                        
                    # Add captured resources to result if any
                    if "captured_by_attacker" in combat_result:
                        result["captured_by_attacker"] = combat_result["captured_by_attacker"]
                        
                    if "captured_by_defenders" in combat_result:
                        result["captured_by_defenders"] = combat_result["captured_by_defenders"]
                else:
                    # No enemy troops, just move
                    update_data = {
                        "location": {
                            "x": action.target_location.x,
                            "y": action.target_location.y
                        },
                        "mode": TroopMode.IDLE.value
                    }
                    
                    update_result = await self.troops_repository.update(troop.id, update_data)
                    if update_result:
                        logger.info(f"Moved troop {troop.id} to ({action.target_location.x}, {action.target_location.y})")
                    else:
                        logger.error(f"Failed to update troop {troop.id} location")
                        result["success"] = False
                        result["error"] = "Failed to update troop location"
                    
                    # Check if we moved to an undefended enemy village - if so, steal resources
                    if target_village and target_village.owner_id != troop.home_id:
                        # Get the home village to check ownership
                        home_village = await self.village_repository.get_by_id(troop.home_id)
                        if home_village and home_village.owner_id != target_village.owner_id:
                            # This is an enemy village with no defending troops, steal resources
                            stolen_resources = await self._steal_resources(
                                attacker_troop=troop,
                                target_village=target_village,
                                new_attacker_quantity=troop.quantity
                            )
                            
                            if any(value > 0 for value in stolen_resources.values()):
                                result["stolen_resources"] = stolen_resources
                                logger.info(f"Troops stole resources from undefended village {target_village.id}")
                    
                    # Check if the target location has a village owned by the same user, if so deposit resources
                    if target_village:
                        logger.info(f"Checking if target village {target_village.id} has a village owned by the same user")
                        if hasattr(troop, 'backpack'):
                            logger.info(f"[RESOURCE_DEBUG] Troop has a backpack, checking ownership")
                            # Get the home village to check ownership
                            home_village = await self.village_repository.get_by_id(troop.home_id)
                            logger.info(f"[RESOURCE_DEBUG] Home village: {home_village}")
                            if home_village and target_village.owner_id == home_village.owner_id:
                                logger.info(f"[RESOURCE_DEBUG] Target village is owned by the same user, depositing resources")
                                # This is a friendly village, deposit resources
                                deposited_resources = await self._deposit_resources(
                                    troop=troop,
                                    target_village=target_village
                                )
                                
                                if any(value > 0 for value in deposited_resources.values()):
                                    result["deposited_resources"] = deposited_resources
                                    logger.info(f"Troops deposited resources to friendly village {target_village.id}")
                    else:
                        logger.info(f"No village found at target location ({action.target_location.x}, {action.target_location.y})")
            
            elif action.action_type == ActionType.ATTACK:
                # Get enemy troops at the target location
                enemy_troops = await self._get_enemy_troops_at_location(
                    troop.home_id, action.target_location.x, action.target_location.y
                )
                
                # Add home villages of all enemy troops to the involved villages
                for enemy_troop in enemy_troops:
                    involved_villages.add(enemy_troop.home_id)
                
                # Find if there's a village at the target location
                target_village = await self.village_repository.find_by_location(
                    action.target_location.x, action.target_location.y
                )
                if target_village:
                    involved_villages.add(target_village.id)
                
                # Update resources for all involved villages before combat
                await self._update_all_village_resources(involved_villages, completion_time)
                
                if enemy_troops:
                    # Combat occurs when there are enemy troops at the target location
                    combat_result = await self._process_combat(
                        attacker_troop=troop,
                        defender_troops=enemy_troops,
                        target_location=action.target_location,
                        is_movement=False,
                        start_location=action.start_location
                    )
                    
                    # For attack actions, we never move the troop to the target location
                    # We just update the troop's mode back to IDLE if it survived
                    if not combat_result["attacker_all_dead"]:
                        await self.troops_repository.update(troop.id, {"mode": TroopMode.IDLE.value})
                        
                    result["combat"] = combat_result
                    
                    # Add stolen resources to result if any
                    if "stolen_resources" in combat_result:
                        result["stolen_resources"] = combat_result["stolen_resources"]
                        
                    # Add captured resources to result if any
                    if "captured_by_attacker" in combat_result:
                        result["captured_by_attacker"] = combat_result["captured_by_attacker"]
                        
                    if "captured_by_defenders" in combat_result:
                        result["captured_by_defenders"] = combat_result["captured_by_defenders"]
                else:
                    # No enemies at target, just update mode back to idle
                    # Even without combat, still update resources for the attacker's home village
                    await self._update_all_village_resources([troop.home_id], completion_time)
                    
                    await self.troops_repository.update(troop.id, {"mode": TroopMode.IDLE.value})
                    logger.info(f"Attack completed for troop {troop.id} but no enemies found at ({action.target_location.x}, {action.target_location.y})")
                    
                    # If there's an enemy village with no defenders, troops should still be able to steal resources during attack
                    if target_village and target_village.owner_id != troop.home_id:
                        # Get the home village to check ownership
                        home_village = await self.village_repository.get_by_id(troop.home_id)
                        if home_village and home_village.owner_id != target_village.owner_id:
                            # This is an enemy village with no defending troops, steal resources
                            stolen_resources = await self._steal_resources(
                                attacker_troop=troop,
                                target_village=target_village,
                                new_attacker_quantity=troop.quantity
                            )
                            
                            if any(value > 0 for value in stolen_resources.values()):
                                result["stolen_resources"] = stolen_resources
                                logger.info(f"Troops stole resources from undefended village {target_village.id}")
            
            # Mark action as processed
            await self.action_repository.mark_processed(action_id)
            
            # Broadcast to all connected users via WebSocket
            await websocket_service.broadcast_troop_action_complete()
            
            return result
            
        except Exception as e:
            logger.error(f"Error completing troop action {action_id}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {"success": False, "error": f"Error completing action: {str(e)}"}
            
    async def _update_all_village_resources(self, village_ids: set, target_time: datetime) -> None:
        """
        Update resources for all villages in the provided list up to the target time.
        
        Args:
            village_ids: Set of village IDs to update
            target_time: The time to update resources until
        """
        # Import here to avoid circular imports
        from minute_empire.services.timed_tasks_service import TimedConstructionService
        
        timed_tasks_service = TimedConstructionService()
        
        for village_id in village_ids:
            try:
                logger.info(f"Updating resources for village {village_id} before troop action")
                await timed_tasks_service.update_resources_until(village_id, target_time)
            except Exception as e:
                logger.error(f"Error updating resources for village {village_id}: {str(e)}")
                logger.error(traceback.format_exc())
    
    async def _get_enemy_troops_at_location(self, home_village_id: str, x: int, y: int) -> List[Any]:
        """
        Get all enemy troops (belonging to a different village) at the given location.
        
        Args:
            home_village_id: The village ID to compare against
            x: X coordinate to check
            y: Y coordinate to check
            
        Returns:
            List of enemy troops at the location
        """
        # Get all troops at the location using the repository
        all_troops = await self.troops_repository.get_troops_at_location(x, y)
        
        # Filter to only include enemy troops (troops from different villages)
        enemy_troops = [troop for troop in all_troops if troop.home_id != home_village_id]
        return enemy_troops
    
    async def _process_combat(
        self, 
        attacker_troop: Any, 
        defender_troops: List[Any],
        target_location: Location,
        is_movement: bool,
        start_location: Location
    ) -> Dict[str, Any]:
        """
        Process combat between attacker and defender troops.
        
        Args:
            attacker_troop: The attacking troop
            defender_troops: List of defending troops
            target_location: The location of the combat
            is_movement: Whether this combat was triggered by movement (True) or attack (False)
            start_location: The starting location of the attacker
            
        Returns:
            Dict containing combat results
        """
        # EVERYTIME YOU CHANGE THE COMBAT LOGIC, YOU NEED TO UPDATE THE README.md FILE FROM SERVICES/README.md
        # Combat constants
        ALL_DEAD_THRESHOLD = 0.85
        ALL_ALIVE_THRESHOLD = 0.15
        ATTACK_SNOWBALL_RATIO = 1.5  # Winner snowball constant
        ATTACKER_DISCOUNT = 0.3  # 30% reduction when attacking defenders in their home village
        
        # Get troop stats from the domain class
        TROOP_STATS = Troop.TROOP_STATS
        
        # Calculate attacker stats
        raw_attacker_atk = attacker_troop.quantity * TROOP_STATS[attacker_troop.type]["atk"]
        raw_attacker_def = attacker_troop.quantity * TROOP_STATS[attacker_troop.type]["def"]
        
        # Calculate defender stats (sum of all defender troops)
        raw_defender_atk = sum(
            troop.quantity * TROOP_STATS[troop.type]["atk"] 
            for troop in defender_troops
        )
        raw_defender_def = sum(
            troop.quantity * TROOP_STATS[troop.type]["def"] 
            for troop in defender_troops
        )
        
        # Apply special rules for archers and pikemen
        # Archer attacking: never takes damage
        if not is_movement and attacker_troop.type == TroopType.ARCHER:
            # Check if target is in valid attack spots
            if {"x": target_location.x, "y": target_location.y} in Troop.get_valid_attack_spots(attacker_troop.type, Location(x=start_location.x, y=start_location.y)):
                # Archer doesn't take damage when attacking
                raw_defender_atk = 0
        
        # Pikeman attacking: doesn't take damage unless attacking its own location
        if not is_movement and attacker_troop.type == TroopType.PIKEMAN:
            # Check if target is in valid attack spots and not at its own location
            if ({"x": target_location.x, "y": target_location.y} in 
                Troop.get_valid_attack_spots(attacker_troop.type, Location(x=start_location.x, y=start_location.y)) and
                not (start_location.x == target_location.x and start_location.y == target_location.y)):
                # Pikeman doesn't take damage when attacking another location
                raw_defender_atk = 0
        
        # Archer defending: cannot attack on its own cell
        for i, defender_troop in enumerate(defender_troops):
            if defender_troop.type == TroopType.ARCHER:
                # If target location is same as defender's location, archer can't attack while defending
                if target_location.x == defender_troop.location.x and target_location.y == defender_troop.location.y:
                    # Subtract this archer's attack contribution from the total defender attack
                    raw_defender_atk -= defender_troop.quantity * TROOP_STATS[defender_troop.type]["atk"]
        
        # Check if any troop is at its home village
        defender_home_bonus = False
        for defender_troop in defender_troops:
            # Find if there's a village at this location
            village_at_location = await self.village_repository.find_by_location(
                target_location.x, target_location.y
            )
            
            if village_at_location:
                # Get the home village of the defender troop to find its owner
                defender_home_village = await self.village_repository.get_by_id(defender_troop.home_id)
                
                # Check if the village at the target location is owned by the same user who owns the defender's home village
                if defender_home_village and village_at_location.owner_id == defender_home_village.owner_id:
                    defender_home_bonus = True
                    break

        # Apply bonuses
        final_attacker_atk = raw_attacker_atk
        final_attacker_def = raw_attacker_def
        final_defender_atk = raw_defender_atk
        final_defender_def = raw_defender_def
        
        # Apply defender's home village bonus (reduction to attacker stats)
        if defender_home_bonus:
            final_attacker_atk = raw_attacker_atk * (1 - ATTACKER_DISCOUNT)
            final_attacker_def = raw_attacker_def * (1 - ATTACKER_DISCOUNT)
            
        # Calculate snowball ratios (power ratios that magnify the effect of strength differences)
        # Avoid division by zero
        attacker_snowball_ratio = 0
        if final_defender_def > 0:
            attacker_snowball_ratio = (final_attacker_atk / final_defender_def) ** ATTACK_SNOWBALL_RATIO
            
        defender_snowball_ratio = 0
        if final_attacker_def > 0:
            defender_snowball_ratio = (final_defender_atk / final_attacker_def) ** ATTACK_SNOWBALL_RATIO
        
        # Calculate loss multipliers (capped between 0 and 1)
        attacker_loss = median([0, defender_snowball_ratio, 1])
        defender_loss = median([0, attacker_snowball_ratio, 1])
        
        # Apply threshold logic: If losses exceed threshold, all troops die
        attacker_all_dead = attacker_loss > ALL_DEAD_THRESHOLD
        defender_all_dead = defender_loss > ALL_DEAD_THRESHOLD
        
        # Apply threshold logic: If losses below threshold, no troops die
        if attacker_loss < ALL_ALIVE_THRESHOLD:
            attacker_loss = 0
        
        if defender_loss < ALL_ALIVE_THRESHOLD:
            defender_loss = 0
            
        # Calculate actual losses
        attacker_quantity_lost = int(attacker_troop.quantity * attacker_loss)
        new_attacker_quantity = attacker_troop.quantity - attacker_quantity_lost

        # Save original quantities and resources for redistribution
        original_attacker_quantity = attacker_troop.quantity
        attacker_backpack = attacker_troop.backpack.dict() if hasattr(attacker_troop, 'backpack') else {}
        
        # Save original defender quantities and resources
        defender_data = []
        for defender_troop in defender_troops:
            defender_backpack = defender_troop.backpack.dict() if hasattr(defender_troop, 'backpack') else {}
            defender_data.append({
                "id": defender_troop.id,
                "type": defender_troop.type,
                "quantity": defender_troop.quantity,
                "backpack": defender_backpack
            })
        
        # Apply losses to attacker
        if attacker_all_dead or new_attacker_quantity <= 0:
            # All attacker troops die - delete them from database instead of marking as DEAD
            await self.troops_repository.delete(attacker_troop.id)
            attacker_all_dead = True
            new_attacker_quantity = 0
        else:
            # Update attacker with new quantity
            await self.troops_repository.update(attacker_troop.id, {
                "quantity": new_attacker_quantity
            })
            
        # Apply losses to each defender troop
        all_defenders_defeated = True
        surviving_defenders = []
        for defender_troop in defender_troops:
            defender_quantity_lost = int(defender_troop.quantity * defender_loss)
            new_defender_quantity = defender_troop.quantity - defender_quantity_lost
            
            if defender_all_dead or new_defender_quantity <= 0:
                # All defender troops die - delete them from database instead of marking as DEAD
                await self.troops_repository.delete(defender_troop.id)
            else:
                # Update defender with new quantity
                await self.troops_repository.update(defender_troop.id, {
                    "quantity": new_defender_quantity
                })
                all_defenders_defeated = False
                surviving_defenders.append({
                    "troop": defender_troop,
                    "new_quantity": new_defender_quantity
                })
        
        # Redistribute resources from fallen troops to survivors
        redistributed_resources = {}
        captured_attacker_resources = {}
        captured_defender_resources = {}
        
        if defender_loss > 0 or attacker_loss > 0:
            # Only redistribute if there are survivors on either side
            redistributed_resources = await self._redistribute_combat_resources(
                attacker_troop=attacker_troop,
                attacker_all_dead=attacker_all_dead,
                original_attacker_quantity=original_attacker_quantity,
                new_attacker_quantity=new_attacker_quantity,
                attacker_backpack=attacker_backpack,
                defender_troops=defender_troops,
                surviving_defenders=surviving_defenders,
                defender_data=defender_data
            )
            
            # Extract relevant data from redistribution result
            if "captured_by_attacker" in redistributed_resources:
                captured_attacker_resources = redistributed_resources["captured_by_attacker"]
            if "captured_by_defenders" in redistributed_resources:
                captured_defender_resources = redistributed_resources["captured_by_defenders"]
        
        # Resource stealing logic from villages
        stolen_resources = {}
        if is_movement and all_defenders_defeated and not attacker_all_dead:
            # Check if there's a village at the target location to steal from
            target_village = await self.village_repository.find_by_location(
                target_location.x, target_location.y
            )
            
            if target_village:
                stolen_resources = await self._steal_resources(
                    attacker_troop=attacker_troop,
                    target_village=target_village,
                    new_attacker_quantity=new_attacker_quantity
                )
        
        # Detailed combat log for debugging
        logger.info(f"Combat result: Attacker loss: {attacker_loss:.2f} ({attacker_quantity_lost} troops), Defender loss: {defender_loss:.2f}")
        logger.info(f"Combat outcome: Attacker all dead: {attacker_all_dead}, All defenders defeated: {all_defenders_defeated}")
        
        combat_result = {
            "attacker_id": attacker_troop.id,
            "defender_ids": [troop.id for troop in defender_troops],
            "attacker_loss": attacker_loss,
            "defender_loss": defender_loss,
            "attacker_all_dead": attacker_all_dead,
            "all_defenders_defeated": all_defenders_defeated,
            "attacker_quantity_lost": attacker_quantity_lost,
            "location": {"x": target_location.x, "y": target_location.y}
        }
        
        # Add stolen resources to result if any
        if stolen_resources:
            combat_result["stolen_resources"] = stolen_resources
            
        # Add captured resources to result if any
        if captured_attacker_resources:
            combat_result["captured_by_attacker"] = captured_attacker_resources
            
        if captured_defender_resources:
            combat_result["captured_by_defenders"] = captured_defender_resources
            
        return combat_result

    async def _redistribute_combat_resources(
        self,
        attacker_troop: Any,
        attacker_all_dead: bool,
        original_attacker_quantity: int,
        new_attacker_quantity: int,
        attacker_backpack: Dict[str, int],
        defender_troops: List[Any],
        surviving_defenders: List[Dict[str, Any]],
        defender_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Redistribute resources from fallen troops to surviving troops based on proportional losses.
        
        Args:
            attacker_troop: The attacking troop
            attacker_all_dead: Whether all attacker troops died
            original_attacker_quantity: Original quantity of attacker troops before combat
            new_attacker_quantity: New quantity of attacker troops after combat
            attacker_backpack: Attacker's backpack resources
            defender_troops: List of all defending troops involved in combat
            surviving_defenders: List of surviving defender troops with new quantities
            defender_data: Original data of defender troops before combat
            
        Returns:
            Dict with resource redistribution results
        """
        logger.info(f"[RESOURCE_DEBUG] Starting resource redistribution | Attacker: {attacker_troop.id} | Original qty: {original_attacker_quantity} → New qty: {new_attacker_quantity} | Attacker dead: {attacker_all_dead}")
        logger.info(f"[RESOURCE_DEBUG] Attacker initial backpack: {attacker_backpack}")
        logger.info(f"[RESOURCE_DEBUG] Defenders: {len(defender_troops)} | Surviving defenders: {len(surviving_defenders)}")
        
        result = {}
        resource_types = ["wood", "stone", "iron", "food"]
        
        # 1. Calculate resources from fallen attacker troops
        attacker_lost_resources = {}
        if original_attacker_quantity > 0 and new_attacker_quantity < original_attacker_quantity:
            # Calculate what proportion of troops were lost
            attacker_loss_ratio = (original_attacker_quantity - new_attacker_quantity) / original_attacker_quantity
            logger.info(f"[RESOURCE_DEBUG] Attacker loss ratio: {attacker_loss_ratio:.4f}")
            
            # Calculate resources lost based on this ratio
            for resource_type in resource_types:
                resource_amount = attacker_backpack.get(resource_type, 0)
                if resource_amount > 0:
                    # Calculate amount lost from fallen troops
                    lost_amount = resource_amount * attacker_loss_ratio
                    attacker_lost_resources[resource_type] = lost_amount
                    
                    # If attacker survived, update their backpack to keep protected resources
                    if not attacker_all_dead:
                        protected_amount = resource_amount - lost_amount
                        attacker_backpack[resource_type] = protected_amount
            
            logger.info(f"[RESOURCE_DEBUG] Attacker lost resources: {attacker_lost_resources}")
            if not attacker_all_dead:
                logger.info(f"[RESOURCE_DEBUG] Attacker kept resources: {attacker_backpack}")
        
        # 2. Calculate resources from fallen defender troops
        defender_lost_resources = {resource_type: 0 for resource_type in resource_types}
        for defender_data_item in defender_data:
            defender_id = defender_data_item["id"]
            original_quantity = defender_data_item["quantity"]
            backpack = defender_data_item.get("backpack", {})
            
            # Find if this defender survived
            survived = False
            new_quantity = 0
            for surviving in surviving_defenders:
                if surviving["troop"].id == defender_id:
                    survived = True
                    new_quantity = surviving["new_quantity"]
                    break
                    
            if original_quantity > 0 and (not survived or new_quantity < original_quantity):
                # Calculate what proportion of troops were lost
                defender_loss_ratio = 1.0 if not survived else (original_quantity - new_quantity) / original_quantity
                logger.info(f"[RESOURCE_DEBUG] Defender {defender_id} loss ratio: {defender_loss_ratio:.4f} | Original: {original_quantity} → New: {new_quantity if survived else 0}")
                logger.info(f"[RESOURCE_DEBUG] Defender {defender_id} initial backpack: {backpack}")
                
                # Calculate resources lost based on this ratio
                defender_troop_lost = {}
                for resource_type in resource_types:
                    resource_amount = backpack.get(resource_type, 0)
                    if resource_amount > 0:
                        lost_amount = resource_amount * defender_loss_ratio
                        defender_lost_resources[resource_type] += lost_amount
                        defender_troop_lost[resource_type] = lost_amount
                        
                        # If defender survived, update their backpack
                        if survived:
                            protected_amount = resource_amount - lost_amount
                            # Get the actual defender troop object
                            for surviving in surviving_defenders:
                                if surviving["troop"].id == defender_id:
                                    defender_troop = surviving["troop"]
                                    
                                    # Update defender's backpack
                                    defender_backpack = defender_troop.backpack.dict() if hasattr(defender_troop, 'backpack') else {}
                                    defender_backpack[resource_type] = protected_amount
                                    
                                    # Save to database
                                    await self.troops_repository.update(defender_id, {
                                        "backpack": defender_backpack
                                    })
                                    break
                
                logger.info(f"[RESOURCE_DEBUG] Defender {defender_id} lost resources: {defender_troop_lost}")
                if survived:
                    current_defender = next((s for s in surviving_defenders if s["troop"].id == defender_id), None)
                    if current_defender:
                        defender_backpack = current_defender["troop"].backpack.dict() if hasattr(current_defender["troop"], 'backpack') else {}
                        logger.info(f"[RESOURCE_DEBUG] Defender {defender_id} kept resources: {defender_backpack}")
        
        logger.info(f"[RESOURCE_DEBUG] Total defender lost resources: {defender_lost_resources}")
        
        # 3. Distribute lost resources to survivors
        captured_by_attacker = {}
        captured_by_defenders = {}
        
        # First, check if there are any resources to distribute
        has_attacker_lost_resources = any(amount > 0 for amount in attacker_lost_resources.values())
        has_defender_lost_resources = any(amount > 0 for amount in defender_lost_resources.values())
        
        logger.info(f"[RESOURCE_DEBUG] Has attacker lost resources: {has_attacker_lost_resources} | Has defender lost resources: {has_defender_lost_resources}")
        
        if has_attacker_lost_resources and len(surviving_defenders) > 0:
            logger.info(f"[RESOURCE_DEBUG] Distributing attacker resources to {len(surviving_defenders)} surviving defenders")
            # Attacker lost resources that can be captured by surviving defenders
            # Calculate total capacity of all surviving defenders
            total_defender_capacity = {}
            for surviving in surviving_defenders:
                defender_troop = surviving["troop"]
                new_quantity = surviving["new_quantity"]
                
                # Get current backpack
                defender_backpack = defender_troop.backpack.dict() if hasattr(defender_troop, 'backpack') else {}
                
                # Calculate remaining capacity
                capacity = Troop.get_backpack_capacity(defender_troop.type, new_quantity)
                remaining_capacity = {
                    resource_type: capacity.get(resource_type, 0) - defender_backpack.get(resource_type, 0) 
                    for resource_type in resource_types
                }
                
                total_defender_capacity[defender_troop.id] = {
                    "remaining": remaining_capacity,
                    "total": capacity.get("total", 0),
                    "current_total": sum(defender_backpack.get(resource_type, 0) for resource_type in resource_types)
                }
                
                logger.info(f"[RESOURCE_DEBUG] Defender {defender_troop.id} capacity: {capacity}")
                logger.info(f"[RESOURCE_DEBUG] Defender {defender_troop.id} remaining capacity: {remaining_capacity}")
            
            # Distribute attacker lost resources to defenders
            for resource_type, lost_amount in attacker_lost_resources.items():
                if lost_amount <= 0:
                    continue
                
                # Calculate total remaining capacity for this resource type across all defenders
                total_capacity_for_resource = sum(
                    data["remaining"].get(resource_type, 0) 
                    for data in total_defender_capacity.values()
                )
                
                logger.info(f"[RESOURCE_DEBUG] Distributing {resource_type}: {lost_amount} | Total defender capacity: {total_capacity_for_resource}")
                
                if total_capacity_for_resource > 0:
                    # Distribute proportionally based on capacity
                    distributed_amount = 0
                    for surviving in surviving_defenders:
                        defender_troop = surviving["troop"]
                        defender_id = defender_troop.id
                        
                        if defender_id not in total_defender_capacity:
                            continue
                        
                        capacity_data = total_defender_capacity[defender_id]
                        resource_capacity = capacity_data["remaining"].get(resource_type, 0)
                        
                        if resource_capacity <= 0:
                            continue
                            
                        # Calculate proportion of total capacity
                        proportion = resource_capacity / total_capacity_for_resource
                        
                        # Calculate amount to give to this defender
                        amount_to_give = min(lost_amount * proportion, resource_capacity)
                        distributed_amount += amount_to_give
                        
                        logger.info(f"[RESOURCE_DEBUG] Giving {resource_type}: {amount_to_give} to defender {defender_id} (proportion: {proportion:.4f})")
                        
                        # Update defender's backpack
                        defender_backpack = defender_troop.backpack.dict() if hasattr(defender_troop, 'backpack') else {}
                        defender_backpack[resource_type] = defender_backpack.get(resource_type, 0) + amount_to_give
                        
                        # Update remaining capacity
                        capacity_data["remaining"][resource_type] -= amount_to_give
                        capacity_data["current_total"] += amount_to_give
                        
                        # Save to database
                        await self.troops_repository.update(defender_id, {
                            "backpack": defender_backpack
                        })
                        
                        logger.info(f"[RESOURCE_DEBUG] Defender {defender_id} updated backpack: {defender_backpack}")
                    
                    # Track captured resources
                    if distributed_amount > 0:
                        captured_by_defenders[resource_type] = distributed_amount
            
            logger.info(f"[RESOURCE_DEBUG] Total captured by defenders: {captured_by_defenders}")
        
        if has_defender_lost_resources and not attacker_all_dead:
            logger.info(f"[RESOURCE_DEBUG] Distributing defender resources to surviving attacker")
            # Defender lost resources that can be captured by surviving attacker
            # Calculate remaining capacity for attacker
            capacity = Troop.get_backpack_capacity(attacker_troop.type, new_attacker_quantity)
            remaining_capacity = {
                resource_type: capacity.get(resource_type, 0) - attacker_backpack.get(resource_type, 0) 
                for resource_type in resource_types
            }
            total_remaining = capacity.get("total", 0) - sum(attacker_backpack.get(resource_type, 0) for resource_type in resource_types)
            
            logger.info(f"[RESOURCE_DEBUG] Attacker capacity: {capacity}")
            logger.info(f"[RESOURCE_DEBUG] Attacker remaining capacity: {remaining_capacity}")
            logger.info(f"[RESOURCE_DEBUG] Attacker total remaining capacity: {total_remaining}")
            
            # Distribute defender lost resources to attacker
            for resource_type, lost_amount in defender_lost_resources.items():
                if lost_amount <= 0:
                    continue
                
                resource_capacity = remaining_capacity.get(resource_type, 0)
                logger.info(f"[RESOURCE_DEBUG] Distributing {resource_type}: {lost_amount} | Attacker capacity: {resource_capacity}")
                
                if resource_capacity > 0:
                    # Calculate amount to give to attacker
                    amount_to_give = min(lost_amount, resource_capacity)
                    
                    # Update attacker's backpack
                    attacker_backpack[resource_type] = attacker_backpack.get(resource_type, 0) + amount_to_give
                    
                    # Update remaining capacity
                    remaining_capacity[resource_type] -= amount_to_give
                    total_remaining -= amount_to_give
                    
                    # Track captured resources
                    captured_by_attacker[resource_type] = amount_to_give
                    
                    logger.info(f"[RESOURCE_DEBUG] Giving {resource_type}: {amount_to_give} to attacker")
            
            # Save attacker's backpack to database
            if any(captured_by_attacker.values()):
                await self.troops_repository.update(attacker_troop.id, {
                    "backpack": attacker_backpack
                })
                logger.info(f"[RESOURCE_DEBUG] Attacker updated backpack: {attacker_backpack}")
            
            logger.info(f"[RESOURCE_DEBUG] Total captured by attacker: {captured_by_attacker}")
        
        # Return results
        if captured_by_attacker:
            result["captured_by_attacker"] = captured_by_attacker
            
        if captured_by_defenders:
            result["captured_by_defenders"] = captured_by_defenders
        
        logger.info(f"[RESOURCE_DEBUG] Redistribution result: {result}")
            
        return result

    async def _steal_resources(self, attacker_troop: Any, target_village: Any, new_attacker_quantity: int) -> Dict[str, float]:
        """
        Calculate and transfer resources from a target village to an attacker's troops
        
        Args:
            attacker_troop: The attacking troop
            target_village: The village to steal from
            new_attacker_quantity: The quantity of attacking troops after combat
            
        Returns:
            Dict with amounts of resources stolen
        """
        logger.info(f"[RESOURCE_DEBUG] Starting resource stealing | Attacker: {attacker_troop.id} | Target: {target_village.id} | Troop qty: {new_attacker_quantity}")
        
        # Calculate troop's backpack capacity
        capacity = Troop.get_backpack_capacity(attacker_troop.type, new_attacker_quantity)
        logger.info(f"[RESOURCE_DEBUG] Attacker capacity: {capacity}")
        
        # Get current backpack content
        current_backpack = attacker_troop.backpack.dict() if hasattr(attacker_troop, 'backpack') else {}
        logger.info(f"[RESOURCE_DEBUG] Current backpack: {current_backpack}")
        
        # Calculate remaining capacity
        remaining_capacity = {
            resource_type: capacity.get(resource_type, 0) - current_backpack.get(resource_type, 0) 
            for resource_type in ["wood", "stone", "iron", "food"]
        }
        logger.info(f"[RESOURCE_DEBUG] Remaining capacity: {remaining_capacity}")
        
        # Initialize stolen resources
        stolen_resources = {"wood": 0, "stone": 0, "iron": 0, "food": 0}
        
        # Get current resources from village
        village_resources = {
            "wood": target_village.resources.wood,
            "stone": target_village.resources.stone,
            "iron": target_village.resources.iron,
            "food": target_village.resources.food
        }
        logger.info(f"[RESOURCE_DEBUG] Village resources: {village_resources}")
        
        # Calculate total resources available in the village
        total_village_resources = sum(village_resources.values())
        
        if total_village_resources <= 0:
            # No resources to steal
            logger.info("[RESOURCE_DEBUG] No resources to steal from village")
            return stolen_resources
            
        # Define resource types
        resource_types = ["wood", "stone", "iron", "food"]
        
        # Calculate max total capacity
        max_total_capacity = capacity["total"] - sum(current_backpack.get(resource_type, 0) for resource_type in resource_types)
        logger.info(f"[RESOURCE_DEBUG] Max total capacity: {max_total_capacity}")
        
        # First pass: Take resources proportionally based on village's resources
        remaining_total_capacity = max_total_capacity
        depleted_resources = []
        
        for resource_type in resource_types:
            if remaining_total_capacity <= 0:
                logger.info("[RESOURCE_DEBUG] No remaining capacity")
                break
                
            # Calculate proportion of this resource in village
            resource_proportion = village_resources[resource_type] / total_village_resources if total_village_resources > 0 else 0
            
            # Calculate how much to steal based on proportion
            to_steal = min(
                remaining_total_capacity * resource_proportion,  # Proportional amount
                remaining_capacity[resource_type],  # Resource-specific capacity
                village_resources[resource_type]  # Available in village
            )
            
            stolen_resources[resource_type] = to_steal
            remaining_total_capacity -= to_steal
            
            logger.info(f"[RESOURCE_DEBUG] First pass stealing {resource_type}: {to_steal} (proportion: {resource_proportion:.4f})")
            
            # Check if we've depleted this resource
            if to_steal >= village_resources[resource_type] - 0.001:  # Using a small epsilon to account for floating point errors
                depleted_resources.append(resource_type)
                logger.info(f"[RESOURCE_DEBUG] Depleted {resource_type} from village")
        
        logger.info(f"[RESOURCE_DEBUG] After first pass - Stolen: {stolen_resources} | Remaining capacity: {remaining_total_capacity} | Depleted: {depleted_resources}")
        
        # Second pass: Redistribute remaining capacity to non-depleted resources
        while remaining_total_capacity > 0.001 and len(depleted_resources) < len(resource_types):
            # Recalculate total available resources excluding depleted ones
            available_resources = {r: village_resources[r] - stolen_resources[r] 
                                 for r in resource_types if r not in depleted_resources}
            
            total_available = sum(available_resources.values())
            if total_available <= 0:
                logger.info("[RESOURCE_DEBUG] No more resources available in second pass")
                break
                
            logger.info(f"[RESOURCE_DEBUG] Second pass - Available resources: {available_resources} | Total available: {total_available}")
                
            # Calculate new proportions
            made_progress = False
            for resource_type, available in available_resources.items():
                if available <= 0:
                    continue
                    
                resource_proportion = available / total_available
                additional_capacity = remaining_capacity[resource_type] - stolen_resources[resource_type]
                
                if additional_capacity <= 0:
                    # Already at capacity for this resource type
                    depleted_resources.append(resource_type)
                    logger.info(f"[RESOURCE_DEBUG] Resource {resource_type} at capacity")
                    continue
                
                # Calculate additional amount to steal
                additional_to_steal = min(
                    remaining_total_capacity * resource_proportion,
                    additional_capacity,
                    available
                )
                
                if additional_to_steal > 0:
                    stolen_resources[resource_type] += additional_to_steal
                    remaining_total_capacity -= additional_to_steal
                    made_progress = True
                    
                    logger.info(f"[RESOURCE_DEBUG] Second pass stealing additional {resource_type}: {additional_to_steal} (proportion: {resource_proportion:.4f})")
                    
                    # Check if depleted
                    if stolen_resources[resource_type] >= village_resources[resource_type] - 0.001:
                        depleted_resources.append(resource_type)
                        logger.info(f"[RESOURCE_DEBUG] Depleted {resource_type} from village in second pass")
                
            # If we couldn't make progress, break
            if not made_progress:
                logger.info("[RESOURCE_DEBUG] Could not make progress in second pass")
                break
        
        logger.info(f"[RESOURCE_DEBUG] Final stolen resources before transfer: {stolen_resources}")
        
        # Now update village and troop resources
        await self._transfer_resources(target_village.id, attacker_troop.id, stolen_resources)
        
        logger.info(f"[RESOURCE_DEBUG] Resources stolen: {stolen_resources} from village {target_village.id} by troop {attacker_troop.id}")
        
        return stolen_resources

    async def _transfer_resources(self, from_village_id: str, to_troop_id: str, resources: Dict[str, float]) -> None:
        """
        Transfer resources from a village to a troop's backpack
        
        Args:
            from_village_id: The ID of the village to take resources from
            to_troop_id: The ID of the troop to receive resources
            resources: Dictionary of resources to transfer
        """
        logger.info(f"[RESOURCE_DEBUG] Transferring resources | From village: {from_village_id} | To troop: {to_troop_id} | Resources: {resources}")
        
        # Round resources to integers to avoid floating point issues
        rounded_resources = {k: round(v) for k, v in resources.items()}
        logger.info(f"[RESOURCE_DEBUG] Rounded resources: {rounded_resources}")
        
        # Get the village
        from minute_empire.domain.village import Village
        village_data = await self.village_repository.get_by_id(from_village_id)
        if not village_data:
            logger.error(f"[RESOURCE_DEBUG] Village {from_village_id} not found when trying to transfer resources")
            return
            
        village = village_data  # It's already a Village object, no need to wrap it
        
        # Get the troop
        troop = await self.troops_repository.get_by_id(to_troop_id)
        if not troop:
            logger.error(f"[RESOURCE_DEBUG] Troop {to_troop_id} not found when trying to transfer resources")
            return
        
        # Log village resources before transfer
        logger.info(f"[RESOURCE_DEBUG] Village resources before transfer: wood={village.resources.wood}, stone={village.resources.stone}, iron={village.resources.iron}, food={village.resources.food}")
            
        # Update troop's backpack
        backpack = troop.backpack.dict() if hasattr(troop, 'backpack') else {}
        logger.info(f"[RESOURCE_DEBUG] Troop backpack before transfer: {backpack}")
        
        resources_modified = False
        
        for resource_type, amount in rounded_resources.items():
            if amount > 0:
                # Deduct from village
                current_village_amount = getattr(village.resources, resource_type, 0)
                if current_village_amount >= amount:
                    setattr(village.resources, resource_type, current_village_amount - amount)
                    resources_modified = True
                    logger.info(f"[RESOURCE_DEBUG] Deducted {amount} {resource_type} from village")
                    
                    # Add to troop
                    backpack[resource_type] = backpack.get(resource_type, 0) + amount
                    logger.info(f"[RESOURCE_DEBUG] Added {amount} {resource_type} to troop")
                else:
                    logger.warning(f"[RESOURCE_DEBUG] Not enough {resource_type} in village: have {current_village_amount}, need {amount}")
        
        # Save changes to village
        if resources_modified:
            # Mark the village as changed which updates the timestamp
            village.mark_as_changed()
            
            # Save the village directly using the repository
            save_result = await self.village_repository.save(village)
            if save_result:
                logger.info(f"[RESOURCE_DEBUG] Village resources after transfer successfully saved: wood={village.resources.wood}, stone={village.resources.stone}, iron={village.resources.iron}, food={village.resources.food}")
            else:
                logger.error(f"[RESOURCE_DEBUG] Failed to save village {from_village_id} after resource transfer")
        
        # Save changes to troop
        if resources_modified:
            await self.troops_repository.update(troop.id, {"backpack": backpack})
            logger.info(f"[RESOURCE_DEBUG] Troop backpack after transfer: {backpack}")
        else:
            logger.info("[RESOURCE_DEBUG] No resources were modified during transfer")

    async def _deposit_resources(self, troop: Any, target_village: Any) -> Dict[str, float]:
        """
        Deposit resources from a troop's backpack into a friendly village.
        If the village storage is full, the excess resources are lost.
        
        Args:
            troop: The troop carrying resources
            target_village: The village to deposit resources into
            
        Returns:
            dict: A dictionary of the deposited resources
        """
        if not hasattr(troop, 'backpack') or not troop.backpack:
            logger.info(f"[RESOURCE_DEBUG] Troop {troop.id} has no backpack or it's empty, nothing to deposit")
            return {"wood": 0, "stone": 0, "iron": 0, "food": 0}
            
        # Convert backpack to dictionary if it's not already
        backpack = troop.backpack
        if hasattr(backpack, 'dict') and callable(getattr(backpack, 'dict')):
            backpack = backpack.dict()
        elif not isinstance(backpack, dict):
            # If it's not a dict and doesn't have a dict method, try to convert it
            try:
                backpack = dict(backpack)
            except:
                # If we can't convert it, just log and continue with original
                logger.error(f"[RESOURCE_DEBUG] Could not convert backpack to dictionary: {troop.backpack}")
        
        logger.info(f"[RESOURCE_DEBUG] Depositing resources from troop {troop.id} to village {target_village.id}")
        logger.info(f"[RESOURCE_DEBUG] Troop backpack before deposit: wood={backpack.get('wood', 0)} stone={backpack.get('stone', 0)} iron={backpack.get('iron', 0)} food={backpack.get('food', 0)}")
        logger.info(f"[RESOURCE_DEBUG] Village resources before deposit: wood={target_village.resources.wood} stone={target_village.resources.stone} iron={target_village.resources.iron} food={target_village.resources.food}")
        
        # Get the village from the repository to ensure we have the correct object
        village = await self.village_repository.get_by_id(target_village.id)
        if not village:
            logger.error(f"Failed to find village {target_village.id} for resource deposit")
            return {"wood": 0, "stone": 0, "iron": 0, "food": 0}
            
        # Calculate available space for each resource
        deposited = {"wood": 0, "stone": 0, "iron": 0, "food": 0}
        
        # Create a new backpack with zero values for existing resources
        new_backpack = {"wood": 0, "stone": 0, "iron": 0, "food": 0}
        for resource_type in ["wood", "stone", "iron", "food"]:
            # Check if resource exists in backpack and has a value greater than 0
            if resource_type in backpack and backpack.get(resource_type, 0) > 0:
                logger.info(f"[RESOURCE_DEBUG] Resource type {resource_type} found in troop backpack")
                
                amount_to_deposit = backpack.get(resource_type, 0)
                logger.info(f"[RESOURCE_DEBUG] Amount to deposit for {resource_type}: {amount_to_deposit}")
                if amount_to_deposit <= 0:
                    continue
                    
                # Calculate available space in the village storage
                current_amount = getattr(village.resources, resource_type, 0)
                logger.info(f"[RESOURCE_DEBUG] Current amount of {resource_type} in village: {current_amount}")
                # Use the calculate_storage_capacity method for the specific resource type
                storage_capacity = village.calculate_storage_capacity(resource_type)
                logger.info(f"[RESOURCE_DEBUG] Storage capacity for {resource_type}: {storage_capacity}")
                available_space = storage_capacity - current_amount
                logger.info(f"[RESOURCE_DEBUG] Available space for {resource_type}: {available_space}")
                
                # Determine how much we can actually deposit
                actual_deposit = min(amount_to_deposit, available_space)
                logger.info(f"[RESOURCE_DEBUG] Actual deposit for {resource_type}: {actual_deposit}")
                if actual_deposit > 0:
                    # Update village resources
                    setattr(village.resources, resource_type, current_amount + actual_deposit)
                    deposited[resource_type] = actual_deposit
                    
                    # Log if some resources were lost due to storage limits
                    if actual_deposit < amount_to_deposit:
                        lost_amount = amount_to_deposit - actual_deposit
                        logger.info(f"[RESOURCE_DEBUG] {lost_amount} {resource_type} was lost because village storage is full")
        
        # Mark village as changed and save it
        village.mark_as_changed()
        try:
            saved = await self.village_repository.save(village)
            if saved:
                logger.info(f"[RESOURCE_DEBUG] Successfully saved village {village.id} after resource deposit")
            else:
                logger.error(f"Failed to save village {village.id} after resource deposit")
        except Exception as e:
            logger.error(f"Error saving village {village.id} after resource deposit: {str(e)}")
        
        # Update the troop's backpack with zero values for all resources
        await self.troops_repository.update(troop.id, {"backpack": new_backpack})
        
        logger.info(f"[RESOURCE_DEBUG] Deposited resources: {deposited}")
        logger.info(f"[RESOURCE_DEBUG] Village resources after deposit: wood={getattr(village.resources, 'wood', 0)} stone={getattr(village.resources, 'stone', 0)} iron={getattr(village.resources, 'iron', 0)} food={getattr(village.resources, 'food', 0)}")
        logger.info(f"[RESOURCE_DEBUG] Troop's new backpack: {new_backpack}")
        
        return deposited 