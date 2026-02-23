"""API v1 router aggregator.

Collects all v1 sub-routers into a single router that gets
mounted at /api/v1 in the main application.
"""

from fastapi import APIRouter

from app.api.v1.workflows import router as workflows_router
from app.api.v1.executions import router as executions_router

api_v1_router = APIRouter()
api_v1_router.include_router(workflows_router)
api_v1_router.include_router(executions_router)