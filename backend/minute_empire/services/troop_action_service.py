from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from bson import ObjectId
from statistics import median
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
        processed_combats = 0
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
                    # Check if there are enemy troops at the target location
                    enemy_troops = await self._get_enemy_troops_at_location(
                        troop.home_id, action.target_location.x, action.target_location.y
                    )
                    
                    if enemy_troops:
                        # Combat occurs when moving to a location with enemy troops
                        combat_result = await self._process_combat(
                            attacker_troop=troop,
                            defender_troops=enemy_troops,
                            target_location=action.target_location,
                            is_movement=True,
                            start_location=action.start_location
                        )
                        processed_combats += 1
                        
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
                                processed_moves += 1
                                print(f"[TroopActionService] MOVE + COMBAT completed: Troop {troop.id} moved from ({action.start_location.x},{action.start_location.y}) to ({action.target_location.x},{action.target_location.y}) after combat")
                            else:
                                errors.append(f"Failed to update troop {troop.id} location after successful combat")
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
                            processed_moves += 1
                            print(f"[TroopActionService] MOVE completed: Troop {troop.id} moved from ({action.start_location.x},{action.start_location.y}) to ({action.target_location.x},{action.target_location.y})")
                        else:
                            errors.append(f"Failed to update troop {troop.id} location for move action")
                
                elif action.action_type == ActionType.ATTACK:
                    # Get enemy troops at the target location
                    enemy_troops = await self._get_enemy_troops_at_location(
                        troop.home_id, action.target_location.x, action.target_location.y
                    )
                    
                    if enemy_troops:
                        # Combat occurs when there are enemy troops at the target location
                        combat_result = await self._process_combat(
                            attacker_troop=troop,
                            defender_troops=enemy_troops,
                            target_location=action.target_location,
                            is_movement=False,
                            start_location=action.start_location
                        )
                        processed_combats += 1
                        processed_attacks += 1
                        
                        # For attack actions, we never move the troop to the target location
                        # We just update the troop's mode back to IDLE if it survived
                        if not combat_result["attacker_all_dead"]:
                            await self.troops_repository.update(troop.id, {"mode": TroopMode.IDLE.value})
                    else:
                        # No enemies at target, just update mode back to idle
                        await self.troops_repository.update(troop.id, {"mode": TroopMode.IDLE.value})
                        processed_attacks += 1
                        print(f"[TroopActionService] ATTACK completed but no enemies found: Troop {troop.id} attacked at ({action.target_location.x},{action.target_location.y})")
                
                # Mark action as processed regardless of type
                await self.action_repository.mark_processed(action.id)
                processed_count += 1
                
            except Exception as e:
                errors.append(f"Error processing action {action.id}: {str(e)}")
                print(f"[TroopActionService] Error processing action {action.id}: {str(e)}")
        
        if processed_count > 0:
            print(f"[TroopActionService] Processed {processed_count} troop actions: {processed_moves} moves, {processed_attacks} attacks, {processed_combats} combats")
        
        return {
            "success": True,
            "processed_count": processed_count,
            "processed_moves": processed_moves,
            "processed_attacks": processed_attacks,
            "processed_combats": processed_combats,
            "errors": errors,
            "message": f"Processed {processed_count} troop actions ({processed_moves} moves, {processed_attacks} attacks, {processed_combats} combats)"
        }
    
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
        
        # Special case: archer and pikeman attack without moving
        # If it's an attack (not movement) and the attacker is archer or pikeman, they don't take damage
        if not is_movement and (attacker_troop.type == TroopType.ARCHER or attacker_troop.type == TroopType.PIKEMAN):
            # Check if current location is in valid attack spots
            if {"x": target_location.x, "y": target_location.y} in Troop.get_valid_attack_spots(attacker_troop.type, Location(x=start_location.x, y=start_location.y)):
                # For archer, it cannot attack current location, so archer never takes damage
                if attacker_troop.type == TroopType.ARCHER:
                    attacker_loss = 0
                
                # For pikeman, it can attack current location, check if the attack is to its own location
                elif attacker_troop.type == TroopType.PIKEMAN:
                    if start_location.x == target_location.x and start_location.y == target_location.y:
                        # If pikeman attacks its own location, it takes damage
                        pass
                    else:
                        # If pikeman attacks another location, it doesn't take damage
                        attacker_loss = 0
        
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
        
        # Apply losses to attacker
        if attacker_all_dead or new_attacker_quantity <= 0:
            # All attacker troops die - delete them from database instead of marking as DEAD
            await self.troops_repository.delete(attacker_troop.id)
            attacker_all_dead = True
        else:
            # Update attacker with new quantity
            await self.troops_repository.update(attacker_troop.id, {
                "quantity": new_attacker_quantity
            })
            
        # Apply losses to each defender troop
        all_defenders_defeated = True
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
        
        # Detailed combat log for debugging
        print(f"[Combat] Attacker: {attacker_troop.type} x{attacker_troop.quantity} (ATK:{raw_attacker_atk}, DEF:{raw_attacker_def})")
        print(f"[Combat] Defenders: {len(defender_troops)} troops (Total ATK:{raw_defender_atk}, Total DEF:{raw_defender_def})")
        print(f"[Combat] After bonuses - Attacker: (ATK:{final_attacker_atk}, DEF:{final_attacker_def}), Defender: (ATK:{final_defender_atk}, DEF:{final_defender_def})")
        print(f"[Combat] Snowball ratios - Attacker: {attacker_snowball_ratio}, Defender: {defender_snowball_ratio}")
        print(f"[Combat] Losses - Attacker: {attacker_loss:.2f} ({attacker_quantity_lost} troops), Defender: {defender_loss:.2f}")
        print(f"[Combat] Results - Attacker all dead: {attacker_all_dead}, All defenders defeated: {all_defenders_defeated}")
        
        return {
            "attacker_id": attacker_troop.id,
            "defender_ids": [troop.id for troop in defender_troops],
            "attacker_loss": attacker_loss,
            "defender_loss": defender_loss,
            "attacker_all_dead": attacker_all_dead,
            "all_defenders_defeated": all_defenders_defeated,
            "attacker_quantity_lost": attacker_quantity_lost,
            "location": {"x": target_location.x, "y": target_location.y}
        } 