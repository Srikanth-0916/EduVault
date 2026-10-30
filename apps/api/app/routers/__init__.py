"""API router package; main.py registers each router under /api/v1."""

from app.routers import auth, users

__all__ = ["auth", "users"]
