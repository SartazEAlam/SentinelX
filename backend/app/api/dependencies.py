"""Shared FastAPI dependencies.

Dependencies are injected into route handlers via FastAPI's Depends() mechanism.
"""

from app.db.database import get_db

# Re-export for convenient importing in route modules
__all__ = ["get_db"]
