"""
Compatibility redirect for MeetLoop FastAPI application.
Re-exports the full MeetLoop app from backend.api.main.
"""

from backend.api.main import app

__all__ = ["app"]