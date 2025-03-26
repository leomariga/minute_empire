from fastapi import FastAPI, HTTPException, Depends, Cookie, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from typing import Optional

from minute_empire.services.registration_service import RegistrationService
from minute_empire.services.authentication_service import AuthenticationService
from minute_empire.services.command_service import CommandService
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
    Location,
    ResourceField
)

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
    """Get all villages owned by the current user."""
    from minute_empire.repositories.village_repository import VillageRepository
    from minute_empire.services.resource_service import ResourceService
    
    # Initialize repositories and services
    village_repo = VillageRepository()
    resource_service = ResourceService()
    
    try:
        # Update resources and get updated villages in one operation
        villages = await resource_service.update_all_user_villages(current_user["id"])
        if not villages:
            return []
            
        # Convert villages to summaries
        village_summaries = []
        for village in villages:
            if village is not None:  # Check if village exists
                summary = village.get_summary()
                if summary:  # Check if summary is not None
                    village_summaries.append(summary)
        
        return village_summaries
    except Exception as e:
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
    from minute_empire.domain.world import World
    from minute_empire.repositories.village_repository import VillageRepository
    from minute_empire.services.resource_service import ResourceService
    import traceback
    
    # Initialize repositories and services
    village_repo = VillageRepository()
    resource_service = ResourceService()
    
    try:
        # Get map bounds from World
        x_min, x_max, y_min, y_max = World.get_map_bounds()
        map_size = World.MAP_SIZE
        
        # Get all villages
        try:
            all_villages = await village_repo.get_all()
            print(f"Retrieved {len(all_villages) if all_villages else 0} villages")
        except Exception as village_error:
            print(f"Error getting villages: {str(village_error)}")
            print(traceback.format_exc())
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
                    # Print village data for debugging
                    print(f"Village {i}: id={village.id}, location={village.location}, type={type(village.location)}")
                    
                    # Extract location safely
                    x, y = 0, 0
                    if hasattr(village.location, 'get'):
                        x = village.location.get("x", 0)
                        y = village.location.get("y", 0)
                    elif hasattr(village.location, 'x') and hasattr(village.location, 'y'):
                        x = village.location.x
                        y = village.location.y
                    
                    # Include resources and city data only for owned villages
                    resource_fields = None
                    city = None
                    if is_owned:
                        # Update resources before sending
                        updated_village = await resource_service.update_village_resources(village.id)
                        print(f"\nProcessing owned village: {village.name}")
                        
                        if updated_village:
                            # Transform resource fields - access directly from _data
                            if hasattr(updated_village._data, 'resource_fields'):
                                print(f"Resource fields found in _data: {updated_village._data.resource_fields}")
                                resource_fields = [
                                    ResourceField(
                                        type=field.type,
                                        level=field.level,
                                        slot=field.slot
                                    ) for field in updated_village._data.resource_fields
                                    if field is not None
                                ]
                                print(f"Converted resource fields: {resource_fields}")
                            else:
                                print("No resource_fields attribute found in _data")
                            
                            # Use city data directly from the village
                            if hasattr(updated_village, 'city'):
                                city = updated_village.city
                    
                    village_data = MapVillage(
                        id=village.id,
                        name=village.name,
                        location=Location(x=x, y=y),
                        owner_id=village.owner_id,
                        is_owned=is_owned,
                        resource_fields=resource_fields if is_owned else None,
                        city=city if is_owned else None
                    )
                    print(f"Final village data resource_fields: {village_data.resource_fields}")
                    villages_data.append(village_data)
            except Exception as village_error:
                print(f"Error processing village {i}: {village_error}")
                print(traceback.format_exc())
                continue
        
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
                villages=villages_data
            )
            return response
        except Exception as response_error:
            print(f"Error creating response: {str(response_error)}")
            print(traceback.format_exc())
            raise HTTPException(
                status_code=500, 
                detail=f"Error creating response: {str(response_error)}"
            )
    except Exception as e:
        print(f"Map info error: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

# Import and include routers
# from app.api.api import api_router
# app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("minute_empire.main:app", host="0.0.0.0", port=8000, reload=True) 