from typing import Dict, Optional, Tuple
from minute_empire.repositories.village_repository import VillageRepository
from minute_empire.domain.village import Village
from minute_empire.schemas.schemas import ResourceFieldType, ConstructionType
from minute_empire.services.resource_service import ResourceService
from minute_empire.services.building_service import BuildingService
from minute_empire.services.resource_field_service import ResourceFieldService

class CommandService:
    """Service for parsing and executing game commands"""
    
    def __init__(self):
        self.village_repository = VillageRepository()
        self.resource_service = ResourceService()
        self.building_service = BuildingService()
        self.resource_field_service = ResourceFieldService()
        
    def parse_command(self, command: str) -> Tuple[str, Dict]:
        """Parse a command string into action and parameters."""
        parts = command.lower().split()
        
        if len(parts) < 4:
            raise ValueError("Invalid command format")
            
        action = parts[0]  # create/upgrade
        if action not in ["create", "upgrade"]:
            raise ValueError(f"Unknown action: {action}")
            
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
            
        elif action == "upgrade":
            if in_index < 2:
                raise ValueError("Invalid upgrade command format")
            target_type = parts[1]
            if target_type not in ["field", "building"]:
                raise ValueError(f"Invalid target type: {target_type}")
                
            return action, {
                "type": target_type,
                "slot": slot
            }

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
                print(f"[CommandService] Delegating field upgrade in slot {slot} to ResourceFieldService")
                result = await self.resource_field_service.upgrade_field(village.id, slot)
                return {
                    "success": result["success"],
                    "message": result.get("error", f"Upgraded field in slot {slot}"),
                    "data": result
                }
                
            elif target_type == "building":
                print(f"[CommandService] Delegating building upgrade in slot {slot} to BuildingService")
                result = await self.building_service.upgrade_building(village.id, slot)
                return {
                    "success": result["success"],
                    "message": result.get("error", f"Upgraded building in slot {slot}"),
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
                print(f"[CommandService] Delegating field creation of type {field_type} to ResourceFieldService")
                result = await self.resource_field_service.add_new_field(village.id, field_type, slot)
                return {
                    "success": result["success"],
                    "message": result.get("error", f"Created {subtype} field in slot {slot}"),
                    "data": result
                }
                
            elif target_type == "building":
                building_type = self._get_construction_type(subtype)
                print(f"[CommandService] Delegating building creation of type {building_type} to BuildingService")
                result = await self.building_service.add_new_building(village.id, building_type, slot)
                return {
                    "success": result["success"],
                    "message": result.get("error", f"Created {subtype} building in slot {slot}"),
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