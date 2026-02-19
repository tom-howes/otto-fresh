"""
Ingest Service API
Exposes the RAG pipeline (ingest, chunk, embed) as HTTP endpoints.
Called by the backend service.
"""
from fastapi import FastAPI
from app.routes.pipeline import router as pipeline_router

app = FastAPI(
    title="Otto Ingest Service",
    description="RAG pipeline: Ingest → Chunk → Embed",
    version="1.0.0"
)

app.include_router(pipeline_router)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "ingest-service"}