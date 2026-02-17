# backend/app/main.py
"""
Otto Backend Service
Authentication, user management, and RAG orchestration
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.auth import router as auth_router
from app.routes.github import router as github_router
from app.routes.user import router as user_router
from app.routes.rag import router as rag_router
from app.routes.webhook import router as webhook_router

app = FastAPI(
    title="Otto Backend Service",
    description="Authentication, user management, and RAG orchestration",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth_router)
app.include_router(github_router)
app.include_router(user_router)
app.include_router(rag_router)
app.include_router(webhook_router)


# Health check for Cloud Run
@app.get("/health")
async def health():
    """Health check endpoint for Cloud Run."""
    return {
        "status": "healthy",
        "service": "backend-service",
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint - service info."""
    return {
        "service": "Otto Backend",
        "status": "running",
        "endpoints": {
            "auth": "/auth",
            "github": "/github", 
            "users": "/users",
            "rag": "/rag",
            "webhooks": "/webhook",
            "health": "/health"
        }
    }