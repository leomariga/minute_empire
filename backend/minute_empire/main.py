from fastapi import FastAPI, HTTPException, Depends, Cookie, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
import asyncio
import logging

from minute_empire.services.registration_service import RegistrationService
from minute_empire.services.authentication_service import AuthenticationService
from minute_empire.services.command_service import CommandService
from minute_empire.services.task_scheduler import task_scheduler
from minute_empire.services.troop_action_service import TroopActionService
from minute_empire.services.timed_tasks_service import TimedConstructionService
from minute_empire.repositories.village_repository import VillageRepository
from datetime import datetime
from minute_empire.api.api_models import (
    RegistrationRequest, 
    RegistrationResponse, 
    LoginRequest, 
    TokenResponse,
    UserResponse,
    VillageResponse,
    CommandRequest,
    CommandResponse,
    MapInfoResponse,
    MapBounds,
    MapVillage,
    UserBasicInfo,
    Location,
    ResourceField,
    ResourceInfo,
    ResourceFieldsInfo,
    CityInfo,
    ConstructionInfo,
    TroopInfo,
    TroopActionInfo
)
from minute_empire.domain.world import World
from minute_empire.domain.building import Building
from minute_empire.domain.resource_field import ResourceProducer
from minute_empire.domain.troop import Troop
from minute_empire.schemas.schemas import ConstructionType, TaskType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Minute Empire API",
    description="FastAPI backend for Minute Empire application",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://localhost:5173",
        "http://localhost",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:5173",
        "http://127.0.0.1",
    ],  # Add your frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OAuth2 scheme for JWT
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Initialize services
auth_service = AuthenticationService()
registration_service = RegistrationService()
troop_action_service = TroopActionService()
timed_tasks_service = TimedConstructionService()
village_repository = VillageRepository()

@app.on_event("startup")
async def startup_event():
    """Initialize services and load all pending tasks on startup"""
    logger.info("Starting Minute Empire API")
    
    # Start the task scheduler
    asyncio.create_task(task_scheduler.run_scheduler())
    
    try:
        now = datetime.utcnow()
        
        # 1. First, complete all tasks that are already due at startup
        # This ensures tasks are completed in the correct chronological order
        completion_results = await timed_tasks_service.complete_all_tasks_until(now)
        
        if completion_results.get("total_tasks_completed", 0) > 0:
            logger.info(f"Completed {completion_results['total_tasks_completed']} overdue tasks at startup")
            logger.info(f"Details: {completion_results['construction_tasks_completed']} construction, "
                       f"{completion_results['troop_training_tasks_completed']} troop training, "
                       f"{completion_results['troop_action_tasks_completed']} troop actions")
        
        # 2. Schedule all future tasks for execution
        scheduling_results = await timed_tasks_service.schedule_pending_tasks(now)
        
        if scheduling_results.get("total_tasks_scheduled", 0) > 0:
            logger.info(f"Scheduled {scheduling_results['total_tasks_scheduled']} future tasks at startup")
            logger.info(f"Details: {scheduling_results['construction_tasks_scheduled']} construction, "
                       f"{scheduling_results['troop_training_tasks_scheduled']} troop training, "
                       f"{scheduling_results['troop_action_tasks_scheduled']} troop actions")
            
        if scheduling_results.get("errors", []):
            for error in scheduling_results["errors"]:
                logger.error(f"Error during task scheduling: {error}")
        
    except Exception as e:
        logger.error(f"Error during startup processing: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

@app.get("/")
async def root():
    return {"message": "Welcome to Minute Empire API"}

@app.post("/register", response_model=RegistrationResponse)
async def register_user(registration: RegistrationRequest, response: Response):
    """
    Register a new user and create their first village.
    
    - **username**: User's username (3-50 characters)
    - **password**: User's password (min 8 characters)
    - **family_name**: User's family name (2-50 characters)
    - **color**: Hex color code for the user (#RRGGBB)
    - **village_name**: Name for the user's first village (3-50 characters)
    """
    try:
        # Use registration service to create user and village
        result = await registration_service.register_user_and_village(
            username=registration.username,
            password=registration.password,
            family_name=registration.family_name,
            color=registration.color,
            village_name=registration.village_name
        )
        
        # Extract user_id and village_id from result
        user_id = result["user_id"]
        village_id = result["village_id"]
        
        # Create JWT token for automatic login
        user_data = await auth_service.get_user_by_id(user_id)
        token = auth_service.create_access_token({"sub": user_id})
        
        # Set cookie with token
        response.set_cookie(
            key="minute_empire_token",
            value=token,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            max_age=60*60*24*7,  # 1 week
            samesite="lax"
        )
        
        return {
            "message": f"Successfully registered user {registration.username} with village {registration.village_name}",
            "user_id": user_id,
            "village_id": village_id
        }
    except ValueError as e:
        # Handle validation errors
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Handle other errors
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.post("/login", response_model=TokenResponse)
async def login(login_request: LoginRequest, response: Response):
    """
    Login with username and password to get an access token.
    
    - **username**: User's username
    - **password**: User's password
    """
    try:
        # Authenticate user using the service
        user = await auth_service.authenticate_user(login_request.username, login_request.password)
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        # Create access token
        token = auth_service.create_access_token({"sub": user["id"]})
        
        # Set cookie with token
        response.set_cookie(
            key="minute_empire_token",
            value=token,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            max_age=60*60*24*7,  # 1 week
            samesite="lax"
        )
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user_id": user["id"],
            "username": user["username"],
            "family_name": user["family_name"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

async def get_current_user(token: Optional[str] = Cookie(None, alias="minute_empire_token")):
    """Get the current authenticated user."""
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        import jwt
        from minute_empire.services.authentication_service import SECRET_KEY, ALGORITHM
        
        # Decode token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Get user from service
        user = await auth_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
            
        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get information about the currently authenticated user."""
    return current_user

@app.get("/logout")
async def logout(response: Response):
    """Logout the current user by clearing the token cookie."""
    response.delete_cookie("minute_empire_token")
    return {"message": "Successfully logged out"}

@app.get("/villages/me")
async def get_my_villages(current_user: dict = Depends(get_current_user)):
    """Get all villages owned by the current user.
    
    Returns a list of village summaries for the current user, with each summary including:
    - Basic village information
    - Resource information
    - Building and construction information
    - Troops owned by the village
    - Active troop actions
    
    This data is used by the frontend to display the village information, including
    the Raw Village Data (JSON) section which shows the complete village data.
    """
    from minute_empire.repositories.village_repository import VillageRepository
    from minute_empire.services.resource_service import ResourceService
    from minute_empire.repositories.troops_repository import TroopsRepository
    from minute_empire.repositories.troop_action_repository import TroopActionRepository
    from minute_empire.services.troop_action_service import TroopActionService
    from datetime import datetime
    import traceback
    
    # Initialize repositories and services
    village_repo = VillageRepository()
    resource_service = ResourceService()
    troops_repo = TroopsRepository()
    troop_action_repo = TroopActionRepository()
    troop_action_service = TroopActionService()
    
    try:
        # Process all pending troop actions first
        try:
            troop_action_result = await troop_action_service.process_pending_troop_actions()
            print(f"Processed troop actions: {troop_action_result['message']}")
            if troop_action_result.get('errors') and len(troop_action_result['errors']) > 0:
                print(f"Troop action errors: {troop_action_result['errors']}")
        except Exception as action_error:
            print(f"Error processing troop actions: {str(action_error)}")
            print(traceback.format_exc())
            # Continue with the rest of the function even if action processing fails
        
        # Update resources and get updated villages in one operation
        villages = await resource_service.update_all_user_villages(current_user["id"])
        if not villages:
            return []
            
        # Convert villages to summaries
        village_summaries = []
        for village in villages:
            try:
                if village is not None:  # Check if village exists
                    summary = village.get_summary()
                    if summary:  # Check if summary is not None
                        # Get troops for this village
                        try:
                            village_troops = await troops_repo.get_by_home(village.id)
                        except Exception as troops_error:
                            print(f"Error getting troops for village {village.id}: {str(troops_error)}")
                            print(traceback.format_exc())
                            village_troops = []  # Continue with empty troops list
                        
                        # Get troop actions for each troop
                        troop_actions = []
                        for troop in village_troops:
                            try:
                                actions = await troop_action_repo.get_active_actions_for_troop(troop.id)
                                if actions:
                                    # Convert each action to a dict with proper datetime handling
                                    for action in actions:
                                        action_dict = action.dict(by_alias=True)
                                        # Ensure datetime fields are properly converted to strings
                                        for field in ["started_at", "completion_time"]:
                                            if field in action_dict and isinstance(action_dict[field], datetime):
                                                action_dict[field] = action_dict[field].isoformat()
                                        troop_actions.append(action_dict)
                            except Exception as actions_error:
                                print(f"Error getting actions for troop {troop.id}: {str(actions_error)}")
                                print(traceback.format_exc())
                                continue  # Skip this troop and continue with the next one
                        
                        # Add troops and troop actions to the summary without modifying the original structure
                        summary_dict = dict(summary)
                        
                        # Convert troops to dict with proper datetime handling
                        troops_list = []
                        for troop in village_troops:
                            try:
                                troop_dict = troop.dict(by_alias=True)
                                # Ensure datetime fields are properly converted to strings
                                for field in ["created_at", "updated_at"]:
                                    if field in troop_dict and isinstance(troop_dict[field], datetime):
                                        troop_dict[field] = troop_dict[field].isoformat()
                                troops_list.append(troop_dict)
                            except Exception as troop_dict_error:
                                print(f"Error converting troop to dict: {str(troop_dict_error)}")
                                print(traceback.format_exc())
                                continue  # Skip this troop and continue with the next one
                        
                        # Add the troops and troop actions to the summary
                        summary_dict["troops"] = troops_list
                        summary_dict["troop_actions"] = troop_actions
                        
                        village_summaries.append(summary_dict)
            except Exception as village_error:
                print(f"Error processing village: {str(village_error)}")
                print(traceback.format_exc())
                continue  # Skip this village and continue with the next one
        
        return village_summaries
    except Exception as e:
        print(f"Error in get_my_villages: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/villages/command", response_model=CommandResponse)
async def execute_command(
    command_request: CommandRequest,
    current_user: dict = Depends(get_current_user)
):
    """Execute a command on a village."""
    from minute_empire.repositories.village_repository import VillageRepository
    
    # Initialize services
    village_repo = VillageRepository()
    command_service = CommandService()
    
    try:
        # Verify village ownership
        village = await village_repo.get_by_id(command_request.village_id)
        if not village:
            raise HTTPException(status_code=404, detail="Village not found")
            
        if village.owner_id != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not your village")
        
        # Execute the command
        result = await command_service.execute_command(
            command=command_request.command,
            village_id=command_request.village_id
        )
        
        return CommandResponse(
            success=result["success"],
            message=result["message"],
            data=result["data"]
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/map/info", response_model=MapInfoResponse)
async def get_map_info(current_user: dict = Depends(get_current_user)):
    """Get map information including bounds and all villages."""
    from minute_empire.repositories.village_repository import VillageRepository
    from minute_empire.services.resource_service import ResourceService
    from minute_empire.repositories.troops_repository import TroopsRepository
    from minute_empire.repositories.troop_action_repository import TroopActionRepository
    from datetime import datetime
    import traceback
    
    # Initialize repositories and services
    village_repo = VillageRepository()
    resource_service = ResourceService()
    troops_repo = TroopsRepository()
    troop_action_repo = TroopActionRepository()
    
    try:
        # Update the user's villages first
        try:
            user_villages = await resource_service.update_all_user_villages(current_user["id"])
            logger.info(f"Updated {len(user_villages)} villages for user {current_user['id']}")
        except Exception as resource_error:
            logger.error(f"Error updating user villages: {str(resource_error)}")
            logger.error(traceback.format_exc())
            # Continue even if resource update fails
        
        # Get map bounds from World
        x_min, x_max, y_min, y_max = World.get_map_bounds()
        map_size = World.MAP_SIZE
        
        # Get all villages
        try:
            all_villages = await village_repo.get_all()
            logger.info(f"Retrieved {len(all_villages) if all_villages else 0} villages")
        except Exception as village_error:
            logger.error(f"Error getting villages: {str(village_error)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500, 
                detail=f"Error retrieving villages: {str(village_error)}"
            )
        
        # Format village data for the map
        villages_data = []
        
        for i, village in enumerate(all_villages or []):
            try:
                if village is not None:
                    is_owned = village.owner_id == current_user["id"]
                    
                    # Extract location safely
                    x, y = 0, 0
                    if hasattr(village.location, 'get'):
                        x = village.location.get("x", 0)
                        y = village.location.get("y", 0)
                    elif hasattr(village.location, 'x') and hasattr(village.location, 'y'):
                        x = village.location.x
                        y = village.location.y
                    
                    # Get user information for the village owner
                    owner = await auth_service.get_user_by_id(village.owner_id)
                    user_info = UserBasicInfo(
                        id=owner["id"],
                        family_name=owner["family_name"],
                        color=owner["color"]
                    )
                    
                    # Initialize village data
                    village_data = MapVillage(
                        id=village.id,
                        name=village.name,
                        location=Location(x=x, y=y),
                        user_info=user_info,
                        is_owned=is_owned
                    )
                    
                    # Only include detailed information for owned villages
                    if is_owned:
                        # Get resource information
                        resource_rates = village.get_resource_rates()
                        resources_info = {}
                        for resource_type in ["wood", "stone", "iron", "food"]:
                            current = getattr(village.resources, resource_type, 0)
                            rate = resource_rates.get(resource_type, 0)
                            capacity = village.calculate_storage_capacity(resource_type)
                            resources_info[resource_type] = ResourceInfo(
                                current=current,
                                rate=rate,
                                capacity=capacity
                            )
                        village_data.resources = resources_info
                        
                        # Add base costs and creation times
                        village_data.base_costs = {
                            "buildings": Building.BASE_CREATION_COSTS,
                            "fields": ResourceProducer.BASE_CREATION_COSTS,
                            "troops": Troop.TRAINING_COSTS
                        }
                        
                        # Base creation times (in minutes)
                        village_data.base_creation_times = {
                            "buildings": Building.BASE_CREATION_TIMES,
                            "fields": ResourceProducer.BASE_CREATION_TIMES,
                            "troops": Troop.TRAINING_TIMES
                        }
                        
                        # Get resource fields information
                        if hasattr(village._data, 'resource_fields'):
                            resource_fields_info = []
                            for field in village._data.resource_fields:
                                if field is not None:
                                    field_producer = village.get_resource_field(field.slot)
                                    if field_producer:
                                        field_info = ResourceFieldsInfo(
                                            type=field.type,
                                            level=field.level,
                                            slot=field.slot,
                                            current_production_rate=field_producer.get_production_rate(),
                                            upgrade_cost=field_producer.get_upgrade_cost(),
                                            upgrade_time=field_producer.get_upgrade_time(),
                                            next_level_production_rate=field_producer.get_production_rate(field.level + 1)
                                        )
                                        resource_fields_info.append(field_info)
                            village_data.resource_fields = resource_fields_info
                        
                        # Get city information
                        if hasattr(village, 'city'):
                            city_info = CityInfo()
                            
                            # Process constructions
                            constructions_info = []
                            for construction in village.city.constructions:
                                building = village.get_building(construction.slot)
                                if building:
                                    # Skip production bonuses for buildings that don't have them
                                    no_bonus_types = [
                                        ConstructionType.BARRAKS, 
                                        ConstructionType.ARCHERY, 
                                        ConstructionType.STABLE,
                                        ConstructionType.RALLY_POINT,
                                        ConstructionType.HIDE_SPOT
                                    ]
                                    
                                    # Base construction info without bonuses
                                    construction_info_data = {
                                        "type": building.type,
                                        "level": building.level,
                                        "slot": building.slot,
                                        "upgrade_cost": building.get_upgrade_cost(),
                                        "upgrade_time": building.get_upgrade_time()
                                    }
                                    
                                    # Add production bonuses only for buildings that have them
                                    if building.type not in no_bonus_types:
                                        construction_info_data["production_bonus"] = building.get_production_bonus()
                                        construction_info_data["next_level_bonus"] = building.get_production_bonus(level=building.level + 1)
                                        
                                    # Create the ConstructionInfo object
                                    construction_info = ConstructionInfo(**construction_info_data)
                                    constructions_info.append(construction_info)
                            
                            city_info.constructions = constructions_info
                            
                            village_data.city = city_info
                        
                        # Add construction tasks directly to the village
                        if hasattr(village._data, 'construction_tasks'):
                            # Only include non-processed tasks
                            village_data.construction_tasks = [
                                task for task in village._data.construction_tasks
                                if not task.processed
                            ]
                            
                        # Add troop training tasks directly to the village
                        if hasattr(village._data, 'troop_training_tasks'):
                            # Only include non-processed tasks
                            village_data.troop_training_tasks = [
                                task for task in village._data.troop_training_tasks
                                if not task.processed
                            ]
                            
                        # Add population information
                        village_data.total_population = village.getTotalPopulation()
                        village_data.working_population = village.getWorkingPopulation()
                
                    villages_data.append(village_data)
            except Exception as village_error:
                logger.error(f"Error processing village {i}: {village_error}")
                logger.error(traceback.format_exc())
                continue
        
        # Get all troops data
        all_troops = []
        try:
            troops = await troops_repo.get_all()
            
            # Process each troop
            for troop in troops:
                troop_data = {
                    "id": troop.id,
                    "type": troop.type,
                    "home_id": troop.home_id, 
                    "quantity": troop.quantity,
                    "location": Location(x=troop.location.x, y=troop.location.y)
                }
                
                # Add mode and backpack only if the user owns the troop
                if any(v.owner_id == current_user["id"] for v in all_villages if v and v.id == troop.home_id):
                    troop_data["mode"] = troop.mode
                    troop_data["backpack"] = troop.backpack
                
                all_troops.append(TroopInfo(**troop_data))
        except Exception as troop_error:
            logger.error(f"Error getting troops: {str(troop_error)}")
            logger.error(traceback.format_exc())
            # Continue with empty troop list
        
        # Get all troop actions data
        all_troop_actions = []
        try:
            # Only get non-processed actions
            actions = await troop_action_repo.get_all_active()
            
            for action in actions:
                if not action.processed:
                    action_data = {
                        "id": action.id,
                        "troop_id": action.troop_id,
                        "action_type": action.action_type,
                        "start_location": Location(x=action.start_location.x, y=action.start_location.y),
                        "target_location": Location(x=action.target_location.x, y=action.target_location.y),
                        "started_at": action.started_at.isoformat(),
                        "completion_time": action.completion_time.isoformat()
                    }
                    all_troop_actions.append(TroopActionInfo(**action_data))
        except Exception as action_error:
            logger.error(f"Error getting troop actions: {str(action_error)}")
            logger.error(traceback.format_exc())
            # Continue with empty actions list
        
        # Create the final response
        try:
            response = MapInfoResponse(
                map_bounds=MapBounds(
                    x_min=x_min,
                    x_max=x_max,
                    y_min=y_min,
                    y_max=y_max
                ),
                map_size=map_size,
                villages=villages_data,
                troops=all_troops,
                troop_actions=all_troop_actions,
                server_time=datetime.utcnow().isoformat()
            )
            return response
        except Exception as response_error:
            logger.error(f"Error creating response: {str(response_error)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500, 
                detail=f"Error creating response: {str(response_error)}"
            )
    except Exception as e:
        logger.error(f"Map info error: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

# Import and include routers
# from app.api.api import api_router
# app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("minute_empire.main:app", host="0.0.0.0", port=8000, reload=True) 