"""Execution REST API endpoints.

Start, cancel, and query workflow executions.
The actual execution runs as a background task — the POST
returns immediately with an execution_id that the frontend
uses to connect via WebSocket.
"""

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.exceptions import NotFoundError
from app.dependencies import get_db, get_redis
from app.models.execution import ExecutionStatus, WorkflowExecution
from app.models.workflow import Workflow
from app.schemas.execution import ExecutionResponse, ExecutionStartRequest
from app.services import execution_engine

router = APIRouter(prefix="/executions", tags=["executions"])


async def _run_in_background(
    workflow_id: uuid.UUID,
    execution_id: uuid.UUID,
    api_keys: dict[str, str],
) -> None:
    """Background task wrapper for workflow execution.

    Creates its own DB session and Redis connection since
    the original request's session is closed by the time
    the background task runs.
    """
    from app.db.session import async_session_factory

    settings = get_settings()
    redis = Redis.from_url(settings.redis_url, decode_responses=True)

    async with async_session_factory() as db:
        try:
            workflow = await db.get(Workflow, workflow_id)
            execution = await db.get(WorkflowExecution, execution_id)

            if not workflow or not execution:
                return

            await execution_engine.run_workflow(
                db=db,
                redis=redis,
                workflow=workflow,
                execution=execution,
                api_keys=api_keys,
            )
        finally:
            await redis.aclose()


@router.post(
    "/workflows/{workflow_id}/execute",
    response_model=ExecutionResponse,
    status_code=201,
)
async def start_execution(
    workflow_id: uuid.UUID,
    data: ExecutionStartRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> ExecutionResponse:
    """Start executing a workflow.

    Creates a WorkflowExecution record and launches the engine
    as a background task. Returns the execution_id immediately
    so the frontend can connect via WebSocket to stream output.
    """
    # Verify workflow exists
    workflow = await db.get(Workflow, workflow_id)
    if not workflow:
        raise NotFoundError("Workflow", str(workflow_id))

    # Merge env-based API keys with request-provided keys
    settings = get_settings()
    api_keys = {**data.api_keys}
    if settings.openai_api_key and "openai" not in api_keys:
        api_keys["openai"] = settings.openai_api_key
    if settings.anthropic_api_key and "anthropic" not in api_keys:
        api_keys["anthropic"] = settings.anthropic_api_key
    if settings.gemini_api_key and "gemini" not in api_keys:
        api_keys["gemini"] = settings.gemini_api_key
    if settings.groq_api_key and "groq" not in api_keys:
        api_keys["groq"] = settings.groq_api_key
    if settings.deepseek_api_key and "deepseek" not in api_keys:
        api_keys["deepseek"] = settings.deepseek_api_key
    if settings.openrouter_api_key and "openrouter" not in api_keys:
        api_keys["openrouter"] = settings.openrouter_api_key

    # Create execution record
    execution = WorkflowExecution(
        workflow_id=workflow_id,
        status=ExecutionStatus.PENDING,
        trigger_input=data.trigger_input,
    )
    db.add(execution)
    await db.commit()
    await db.refresh(execution)

    # Launch background task
    background_tasks.add_task(
        _run_in_background,
        workflow_id,
        execution.id,
        api_keys,
    )

    return ExecutionResponse.model_validate(execution)


@router.post("/{execution_id}/cancel", status_code=200)
async def cancel_execution(execution_id: uuid.UUID) -> dict:
    """Cancel a running execution."""
    execution_engine.cancel_execution(str(execution_id))
    return {"status": "cancellation_requested", "execution_id": str(execution_id)}


@router.get("/{execution_id}", response_model=ExecutionResponse)
async def get_execution(
    execution_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ExecutionResponse:
    """Get execution status and results."""
    execution = await db.get(WorkflowExecution, execution_id)
    if not execution:
        raise NotFoundError("Execution", str(execution_id))
    return ExecutionResponse.model_validate(execution)