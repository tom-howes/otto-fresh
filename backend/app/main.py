
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.auth import router as auth_router
from app.routes.github import router as github_router
from app.routes.user import router as user_router
from app.routes.rag import router as rag_router # Add this
from app.config import FRONTEND_URL 

# Initialize Fast API App
app = FastAPI()

#CORS Configuration - IMPORTANT for frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        FRONTEND_URL,  # http://localhost:3000
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,  # Required for cookies
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_router)
app.include_router(github_router)
app.include_router(user_router)
app.include_router(rag_router)
