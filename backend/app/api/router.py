from fastapi import APIRouter

from app.api.routes import audit, health, packages


api_router = APIRouter(prefix="/api")
api_router.include_router(health.router, tags=["health"])
api_router.include_router(packages.router, prefix="/packages", tags=["packages"])
api_router.include_router(audit.router, prefix="/audit-events", tags=["audit-events"])
