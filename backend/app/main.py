from fastapi import FastAPI
from app.routes.auth import router as auth_router

# Initialize Fast API App
app = FastAPI()

# Include Routers
app.include_router(auth_router)