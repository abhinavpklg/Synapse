"""Pydantic schemas for execution API requests and responses."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ExecutionStartRequest(BaseModel):
    """Request body to start a workflow execution."""

    trigger_input: dict = Field(
        default_factory=dict,
        description="Initial input data, e.g. {'input': 'Write about quantum computing'}",
    )
    api_keys: dict[str, str] = Field(
        default_factory=dict,
        description="Provider API keys, e.g. {'openai': 'sk-...'}",
    )


class ExecutionResponse(BaseModel):
    """Response body for an execution record."""

    id: uuid.UUID
    workflow_id: uuid.UUID
    status: str
    trigger_input: dict
    started_at: datetime | None
    completed_at: datetime | None
    error: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}