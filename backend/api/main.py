"""
FastAPI Application Entry Point for MeetLoop.

Wraps the LangGraph StateGraph engine and exposes REST endpoints
for the React frontend, demo tooling, and judging interface.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import router

app = FastAPI(
    title="MeetLoop — AI Meeting Auditor",
    description="Cross-meeting intelligence, pattern analysis, and pre-meeting briefing agent.",
    version="1.0.0",
)

# Enable CORS for React frontend (Vite default port 5173, Create-React-App 3000, and production origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(router)


@app.get("/")
async def root():
    return {
        "message": "MeetLoop Agent API is live!",
        "endpoints": {
            "health": "/health",
            "fixtures": "/fixtures",
            "run": "POST /run",
            "docs": "/docs",
        }
    }
