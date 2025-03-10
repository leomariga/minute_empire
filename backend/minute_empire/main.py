from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Minute Empire API",
    description="FastAPI backend for Minute Empire application",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],  # Vue.js frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to Minute Empire API"}

# Import and include routers
# from app.api.api import api_router
# app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("minute_empire.main:app", host="0.0.0.0", port=8000, reload=True) 