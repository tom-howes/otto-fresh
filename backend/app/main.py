from fastapi import FastAPI
from app.routes.auth import router as auth_router
from app.routes.github import router as github_router
from app.routes.user import router as user_router
from app.routes.rag import router as rag_router  # Add this

# Initialize Fast API App
app = FastAPI()

# Include Routers
app.include_router(auth_router)
app.include_router(github_router)
app.include_router(user_router)
app.include_router(rag_router)