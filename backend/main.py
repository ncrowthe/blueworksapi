"""
FastAPI application entry point for the Blueworks Live backend.

Start the server with:
    uvicorn backend.main:app --reload
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.routes import diagram, glossary, process, search

app = FastAPI(title="Blueworks Live API")


# -- Health check --------------------------------------------------------------
@app.get("/api/health")
def health() -> dict:
    """Liveness probe — returns {"status": "ok"}."""
    return {"status": "ok"}


# -- API routers ---------------------------------------------------------------
app.include_router(search.router, prefix="/api")
app.include_router(process.router, prefix="/api")
app.include_router(diagram.router, prefix="/api")
app.include_router(glossary.router, prefix="/api")


# -- Static files (React build) ------------------------------------------------
# The Dockerfile copies frontend/dist → backend/static/ (Sub-Task 8).
# Wrapped in try/except so the server starts cleanly during development
# before the React app has been built.
try:
    app.mount("/", StaticFiles(directory="backend/static", html=True), name="static")
except RuntimeError:
    pass  # backend/static does not exist yet; API endpoints are still reachable
