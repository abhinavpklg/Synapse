"""Workflow business logic service.

Handles CRUD operations for workflows. This layer sits between
the API routes (thin HTTP layer) and the database (SQLAlchemy).
Routes never import SQLAlchemy directly — they go through services.
"""

import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.models.workflow import Workflow
from app.schemas.workflow import WorkflowCreate, WorkflowUpdate

logger = get_logger(__name__)


async def create_workflow(db: AsyncSession, data: WorkflowCreate) -> Workflow:
    """Create a new workflow.

    Args:
        db: Database session.
        data: Validated workflow creation data.

    Returns:
        The created workflow with generated ID and timestamps.
    """
    workflow = Workflow(
        name=data.name,
        description=data.description,
        canvas_data=data.canvas_data,
        is_template=data.is_template,
    )
    db.add(workflow)
    await db.flush()
    await db.refresh(workflow)
    logger.info("workflow_created", workflow_id=str(workflow.id), name=workflow.name)
    return workflow


async def get_workflow(db: AsyncSession, workflow_id: uuid.UUID) -> Workflow:
    """Get a workflow by ID.

    Args:
        db: Database session.
        workflow_id: UUID of the workflow.

    Returns:
        The workflow.

    Raises:
        NotFoundError: If the workflow doesn't exist.
    """
    workflow = await db.get(Workflow, workflow_id)
    if not workflow:
        raise NotFoundError("Workflow", str(workflow_id))
    return workflow


async def list_workflows(
    db: AsyncSession,
    *,
    templates_only: bool = False,
) -> tuple[list[Workflow], int]:
    """List all workflows, optionally filtered to templates only.

    Args:
        db: Database session.
        templates_only: If True, only return template workflows.

    Returns:
        Tuple of (workflow list, total count).
    """
    query = select(Workflow).order_by(Workflow.updated_at.desc())
    count_query = select(func.count()).select_from(Workflow)

    if templates_only:
        query = query.where(Workflow.is_template.is_(True))
        count_query = count_query.where(Workflow.is_template.is_(True))

    result = await db.execute(query)
    workflows = list(result.scalars().all())

    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    return workflows, total


async def update_workflow(
    db: AsyncSession,
    workflow_id: uuid.UUID,
    data: WorkflowUpdate,
) -> Workflow:
    """Update an existing workflow.

    Only fields present in the update payload are changed.

    Args:
        db: Database session.
        workflow_id: UUID of the workflow to update.
        data: Validated update data (partial).

    Returns:
        The updated workflow.

    Raises:
        NotFoundError: If the workflow doesn't exist.
    """
    workflow = await get_workflow(db, workflow_id)

    update_fields = data.model_dump(exclude_unset=True)
    for field, value in update_fields.items():
        setattr(workflow, field, value)

    await db.flush()
    await db.refresh(workflow)
    logger.info("workflow_updated", workflow_id=str(workflow_id), fields=list(update_fields.keys()))
    return workflow


async def delete_workflow(db: AsyncSession, workflow_id: uuid.UUID) -> None:
    """Delete a workflow by ID.

    Args:
        db: Database session.
        workflow_id: UUID of the workflow to delete.

    Raises:
        NotFoundError: If the workflow doesn't exist.
    """
    workflow = await get_workflow(db, workflow_id)
    await db.delete(workflow)
    await db.flush()
    logger.info("workflow_deleted", workflow_id=str(workflow_id))