from fastapi import FastAPI, HTTPException, Depends, Cookie, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from typing import Optional

from minute_empire.core.registration import create_user_and_village
from minute_empire.core.authentication import authenticate_user, create_access_token, get_user_by_id, get_user_villages
from minute_empire.api.api_models import (
    RegistrationRequest, 
    RegistrationResponse, 
    LoginRequest, 
    TokenResponse,
    UserResponse,
    VillageResponse
)

app = FastAPI(
    title="Minute Empire API",
    description="FastAPI backend for Minute Empire application",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://localhost:5173"],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OAuth2 scheme for JWT
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

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
        # Call the create_user_and_village function
        result = await create_user_and_village(
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
        user_data = await get_user_by_id(user_id)
        token = create_access_token({"sub": user_id})
        
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
        # Authenticate user
        user = await authenticate_user(login_request.username, login_request.password)
        
        # Create access token
        token = create_access_token({"sub": user["_id"]})
        
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
            "user_id": user["_id"],
            "username": user["username"],
            "family_name": user["family_name"]
        }
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
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
        from minute_empire.core.authentication import SECRET_KEY, ALGORITHM
        
        # Decode token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Get user from database
        user = await get_user_by_id(user_id)
        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get information about the currently authenticated user."""
    return {
        "id": current_user["_id"],
        "username": current_user["username"],
        "family_name": current_user["family_name"],
        "color": current_user["color"]
    }

@app.get("/logout")
async def logout(response: Response):
    """Logout the current user by clearing the token cookie."""
    response.delete_cookie("minute_empire_token")
    return {"message": "Successfully logged out"}

@app.get("/villages/me")
async def get_my_villages(current_user: dict = Depends(get_current_user)):
    """Get all villages owned by the current user."""
    villages = await get_user_villages(current_user["_id"])
    return villages

# Import and include routers
# from app.api.api import api_router
# app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("minute_empire.main:app", host="0.0.0.0", port=8000, reload=True) 