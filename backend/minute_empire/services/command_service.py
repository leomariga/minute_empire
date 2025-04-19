from typing import Dict, Optional, Tuple
from minute_empire.repositories.village_repository import VillageRepository
from minute_empire.domain.village import Village
from minute_empire.schemas.schemas import ResourceFieldType, ConstructionType, TroopType
from minute_empire.services.resource_service import ResourceService
from minute_empire.services.building_service import BuildingService
from minute_empire.services.resource_field_service import ResourceFieldService
from minute_empire.services.timed_tasks_service import TimedConstructionService
from minute_empire.services.troop_action_service import TroopActionService

class CommandService:
    """Service for parsing and executing game commands"""
    
    def __init__(self):
        self.village_repository = VillageRepository()
        self.resource_service = ResourceService()
        self.building_service = BuildingService()
        self.resource_field_service = ResourceFieldService()
        self.construction_service = TimedConstructionService()
        
    def parse_command(self, command: str) -> Tuple[str, Dict]:
        """Parse a command string into action and parameters."""
        parts = command.lower().split()
        
        if len(parts) < 2:
            raise ValueError("Invalid command format")
            
        action = parts[0]  # create/upgrade/train/move/attack/destroy
        
        # Handle existing commands first
        if action in ["create", "upgrade", "destroy", "train"]:
            if action == "train":
                if len(parts) < 3:
                    raise ValueError("Invalid train command format")
                quantity = int(parts[1])
                troop_type = parts[2]
                return action, {
                    "troop_type": troop_type,
                    "quantity": quantity
                }
            
            if "in" not in parts:
                raise ValueError("Missing 'in' keyword")
            
            in_index = parts.index("in")
            
            try:
                slot = int(parts[in_index + 1])
            except (IndexError, ValueError):
                raise ValueError("Invalid slot number")
            
            if action == "create":
                if in_index < 3:
                    raise ValueError("Invalid create command format")
                subtype = parts[1]
                target_type = parts[2]
                if target_type not in ["field", "building"]:
                    raise ValueError(f"Invalid target type: {target_type}")
                
                return action, {
                    "type": target_type,
                    "subtype": subtype,
                    "slot": slot
                }
            
            elif action in ["upgrade", "destroy"]:
                if in_index < 2:
                    raise ValueError(f"Invalid {action} command format")
                target_type = parts[1]
                if target_type not in ["field", "building"]:
                    raise ValueError(f"Invalid target type: {target_type}")
                
                return action, {
                    "type": target_type,
                    "slot": slot
                }

        # Handle new troop action commands
        elif action in ["move", "attack"]:
            if len(parts) < 4 or "to" not in parts:
                raise ValueError(f"Invalid {action} command format. Use: {action} [troop_id] to [x,y]")
            
            troop_id = parts[1]
            
            # Find the 'to' keyword
            to_index = parts.index("to")
            if to_index + 1 >= len(parts):
                raise ValueError(f"Missing location after 'to' in {action} command")
            
            # Parse location - could be "x,y" or separate "x y"
            location_part = parts[to_index + 1]
            if ',' in location_part:
                # Format: "move troop_id to x,y"
                try:
                    x, y = map(int, location_part.split(','))
                except ValueError:
                    raise ValueError(f"Invalid location format: {location_part}. Use: x,y")
            else:
                # Format: "move troop_id to x y"
                if to_index + 2 >= len(parts):
                    raise ValueError(f"Incomplete location in {action} command")
                try:
                    x = int(parts[to_index + 1])
                    y = int(parts[to_index + 2])
                except ValueError:
                    raise ValueError("Location coordinates must be integers")
            
            return action, {
                "troop_id": troop_id,
                "target_x": x,
                "target_y": y
            }
        
        else:
            raise ValueError(f"Unknown action: {action}")

    def _get_resource_field_type(self, type_str: str) -> ResourceFieldType:
        """Convert string to ResourceFieldType enum."""
        try:
            return ResourceFieldType[type_str.upper()]
        except KeyError:
            raise ValueError(f"Invalid resource field type: {type_str}")
    
    def _get_construction_type(self, type_str: str) -> ConstructionType:
        """Convert string to ConstructionType enum."""
        try:
            return ConstructionType[type_str.upper()]
        except KeyError:
            raise ValueError(f"Invalid construction type: {type_str}")
    
    def _get_troop_type(self, type_str: str) -> TroopType:
        """Convert string to TroopType enum."""
        try:
            return TroopType[type_str.upper()]
        except KeyError:
            raise ValueError(f"Invalid troop type: {type_str}")
    
    async def execute_command(self, command: str, village_id: str) -> Dict:
        """Execute a command on a village."""
        print(f"[CommandService] Executing command: {command} for village {village_id}")
        
        # Get the village
        village = await self.village_repository.get_by_id(village_id)
        if not village:
            return {"success": False, "message": "Village not found", "data": {}}
            
        # Parse the command
        try:
            action, params = self.parse_command(command)
        except ValueError as e:
            return {"success": False, "message": str(e), "data": {}}
            
        # Execute the appropriate action
        try:
            if action == "create":
                return await self._handle_create(village, params)
            elif action == "upgrade":
                return await self._handle_upgrade(village, params)
            elif action == "destroy":
                return await self._handle_destroy(village, params)
            elif action == "train":
                return await self._handle_train(village, params)
            elif action == "move":
                return await self._handle_move(village, params)
            elif action == "attack":
                return await self._handle_attack(village, params)
            else:
                return {
                    "success": False,
                    "message": f"Unknown action: {action}",
                    "data": {}
                }
        except Exception as e:
            print(f"[CommandService] Error executing command: {str(e)}")
            return {
                "success": False,
                "message": f"Error executing command: {str(e)}",
                "data": {}
            }
    
    async def _handle_upgrade(self, village: Village, params: Dict) -> Dict:
        """Handle upgrade commands."""
        print(f"[CommandService] Handling upgrade command for village {village.id}")
        target_type = params["type"]
        slot = params["slot"]
        
        try:
            if target_type == "field":
                print(f"[CommandService] Starting field upgrade in slot {slot} using ConstructionService")
                result = await self.construction_service.start_field_upgrade(village.id, slot)
                return {
                    "success": result["success"],
                    "message": result.get("error", f"Started upgrade of field in slot {slot}"),
                    "data": result
                }
                
            elif target_type == "building":
                print(f"[CommandService] Starting building upgrade in slot {slot} using ConstructionService")
                result = await self.construction_service.start_building_upgrade(village.id, slot)
                return {
                    "success": result["success"],
                    "message": result.get("error", f"Started upgrade of building in slot {slot}"),
                    "data": result
                }
            
            raise ValueError(f"Invalid upgrade type: {target_type}")
        except Exception as e:
            print(f"[CommandService] Error in upgrade command: {str(e)}")
            return {
                "success": False,
                "message": str(e),
                "data": {}
            }
    
    async def _handle_create(self, village: Village, params: Dict) -> Dict:
        """Handle create commands."""
        print(f"[CommandService] Handling create command for village {village.id}")
        target_type = params["type"]
        subtype = params["subtype"]
        slot = params["slot"]
        
        try:
            if target_type == "field":
                field_type = self._get_resource_field_type(subtype)
                print(f"[CommandService] Starting field construction of type {field_type} using ConstructionService")
                result = await self.construction_service.start_field_construction(village.id, field_type, slot)
                return {
                    "success": result["success"],
                    "message": result.get("error", f"Started construction of {subtype} field in slot {slot}"),
                    "data": result
                }
                
            elif target_type == "building":
                building_type = self._get_construction_type(subtype)
                print(f"[CommandService] Starting building construction of type {building_type} using ConstructionService")
                result = await self.construction_service.start_building_construction(village.id, building_type, slot)
                return {
                    "success": result["success"],
                    "message": result.get("error", f"Started construction of {subtype} building in slot {slot}"),
                    "data": result
                }
            
            raise ValueError(f"Invalid create type: {target_type}")
        except Exception as e:
            print(f"[CommandService] Error in create command: {str(e)}")
            return {
                "success": False,
                "message": str(e),
                "data": {}
            }
    
    async def _handle_train(self, village: Village, params: Dict) -> Dict:
        """Handle train commands."""
        print(f"[CommandService] Handling train command for village {village.id}")
        troop_type_str = params["troop_type"]
        quantity = params["quantity"]
        
        try:
            # Convert string to TroopType enum
            troop_type = self._get_troop_type(troop_type_str)
            
            # Validate and start troop training
            result = await self.construction_service.start_troop_training(village.id, troop_type, quantity)
            return {
                "success": result["success"],
                "message": result.get("error", f"Started training {quantity} {troop_type_str}(s)"),
                "data": result
            }
        except Exception as e:
            print(f"[CommandService] Error in train command: {str(e)}")
            return {
                "success": False,
                "message": str(e),
                "data": {}
            }
    
    async def _handle_move(self, village: Village, params: Dict) -> Dict:
        """Handle move commands."""
        print(f"[CommandService] Handling move command for troop {params['troop_id']}")
        
        # Initialize troop action service
        troop_action_service = TroopActionService()
        
        try:
            # Start the movement action, passing village.id for ownership verification
            result = await troop_action_service.start_move_action(
                troop_id=params["troop_id"],
                target_x=params["target_x"],
                target_y=params["target_y"],
                village_id=village.id  # Pass the village ID for ownership verification
            )
            
            if not result["success"]:
                print(f"[CommandService] Move command failed: {result.get('error', 'Unknown error')}")
                
            return {
                "success": result["success"],
                "message": result.get("error", result.get("message", "Started troop movement")),
                "data": {
                    "troop_id": params["troop_id"],
                    "target_location": {"x": params["target_x"], "y": params["target_y"]},
                    "action_id": result.get("action_id"),
                    "estimated_completion": result.get("estimated_completion")
                }
            }
        except Exception as e:
            error_msg = f"Error in move command: {str(e)}"
            print(f"[CommandService] {error_msg}")
            import traceback
            print(f"[CommandService] Traceback: {traceback.format_exc()}")
            return {
                "success": False,
                "message": error_msg,
                "data": {
                    "troop_id": params["troop_id"],
                    "target_location": {"x": params["target_x"], "y": params["target_y"]},
                    "error_details": str(e)
                }
            }
    
    async def _handle_attack(self, village: Village, params: Dict) -> Dict:
        """Handle attack commands."""
        print(f"[CommandService] Handling attack command for troop {params['troop_id']}")
        
        # Initialize troop action service
        troop_action_service = TroopActionService()
        
        try:
            # Start the attack action, passing village.id for ownership verification
            result = await troop_action_service.start_attack_action(
                troop_id=params["troop_id"],
                target_x=params["target_x"],
                target_y=params["target_y"],
                village_id=village.id  # Pass the village ID for ownership verification
            )
            
            if not result["success"]:
                print(f"[CommandService] Attack command failed: {result.get('error', 'Unknown error')}")
                
            return {
                "success": result["success"],
                "message": result.get("error", result.get("message", "Started troop attack on target location")),
                "data": {
                    "troop_id": params["troop_id"],
                    "target_location": {"x": params["target_x"], "y": params["target_y"]},
                    "action_id": result.get("action_id"),
                    "estimated_completion": result.get("estimated_completion")
                }
            }
        except Exception as e:
            error_msg = f"Error in attack command: {str(e)}"
            print(f"[CommandService] {error_msg}")
            import traceback
            print(f"[CommandService] Traceback: {traceback.format_exc()}")
            return {
                "success": False,
                "message": error_msg,
                "data": {
                    "troop_id": params["troop_id"],
                    "target_location": {"x": params["target_x"], "y": params["target_y"]},
                    "error_details": str(e)
                }
            }
    
    async def _handle_destroy(self, village: Village, params: Dict) -> Dict:
        """Handle destroy commands."""
        print(f"[CommandService] Handling destroy command for village {village.id}")
        target_type = params["type"]
        slot = params["slot"]
        
        try:
            if target_type == "field":
                print(f"[CommandService] Starting field destruction in slot {slot} using ConstructionService")
                result = await self.construction_service.start_field_destruction(village.id, slot)
                return {
                    "success": result["success"],
                    "message": result.get("error", f"Started destruction of field in slot {slot}"),
                    "data": result
                }
                
            elif target_type == "building":
                print(f"[CommandService] Starting building destruction in slot {slot} using ConstructionService")
                result = await self.construction_service.start_building_destruction(village.id, slot)
                return {
                    "success": result["success"],
                    "message": result.get("error", f"Started destruction of building in slot {slot}"),
                    "data": result
                }
            
            raise ValueError(f"Invalid destroy type: {target_type}")
        except Exception as e:
            print(f"[CommandService] Error in destroy command: {str(e)}")
            return {
                "success": False,
                "message": str(e),
                "data": {}
            } 