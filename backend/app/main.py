# Update backend/app/main.py
from fastapi import FastAPI
from app.routes.auth import router as auth_router
from app.routes.github import router as github_router
from app.routes.user import router as user_router
from app.routes.rag import router as rag_router
from app.routes.webhook import router as webhook_router  # NEW

app = FastAPI()

app.include_router(auth_router)
app.include_router(github_router)
app.include_router(user_router)
app.include_router(rag_router)
app.include_router(webhook_router)  # NEW