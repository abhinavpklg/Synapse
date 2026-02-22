"""Workflow REST API endpoints.

Thin HTTP layer — validates requests via Pydantic schemas,
delegates to workflow_service for business logic, returns responses.
"""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.schemas.workflow import (
    WorkflowCreate,
    WorkflowListResponse,
    WorkflowResponse,
    WorkflowUpdate,
)
from app.services import workflow_service

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.post("", response_model=WorkflowResponse, status_code=201)
async def create_workflow(
    data: WorkflowCreate,
    db: AsyncSession = Depends(get_db),
) -> WorkflowResponse:
    """Create a new workflow."""
    workflow = await workflow_service.create_workflow(db, data)
    return WorkflowResponse.model_validate(workflow)


@router.get("", response_model=WorkflowListResponse)
async def list_workflows(
    templates_only: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
) -> WorkflowListResponse:
    """List all workflows."""
    workflows, total = await workflow_service.list_workflows(
        db, templates_only=templates_only,
    )
    return WorkflowListResponse(
        workflows=[WorkflowResponse.model_validate(w) for w in workflows],
        total=total,
    )


@router.get("/templates", response_model=WorkflowListResponse)
async def list_templates(
    db: AsyncSession = Depends(get_db),
) -> WorkflowListResponse:
    """List template workflows only."""
    workflows, total = await workflow_service.list_workflows(
        db, templates_only=True,
    )
    return WorkflowListResponse(
        workflows=[WorkflowResponse.model_validate(w) for w in workflows],
        total=total,
    )


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> WorkflowResponse:
    """Get a single workflow by ID."""
    workflow = await workflow_service.get_workflow(db, workflow_id)
    return WorkflowResponse.model_validate(workflow)


@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: uuid.UUID,
    data: WorkflowUpdate,
    db: AsyncSession = Depends(get_db),
) -> WorkflowResponse:
    """Update an existing workflow."""
    workflow = await workflow_service.update_workflow(db, workflow_id, data)
    return WorkflowResponse.model_validate(workflow)


@router.delete("/{workflow_id}", status_code=204)
async def delete_workflow(
    workflow_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a workflow."""
    await workflow_service.delete_workflow(db, workflow_id)