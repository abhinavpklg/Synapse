"""Pydantic schemas for workflow API requests and responses.

These schemas validate incoming data and serialize outgoing data.
They are separate from the SQLAlchemy ORM models — schemas define
the API contract, models define the database structure.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class WorkflowCreate(BaseModel):
    """Request body for creating a new workflow."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(default="")
    canvas_data: dict = Field(default_factory=dict)
    is_template: bool = Field(default=False)


class WorkflowUpdate(BaseModel):
    """Request body for updating an existing workflow.

    All fields are optional — only provided fields are updated.
    """

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    canvas_data: dict | None = None
    is_template: bool | None = None


class WorkflowResponse(BaseModel):
    """Response body for a single workflow."""

    id: uuid.UUID
    name: str
    description: str
    canvas_data: dict
    is_template: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WorkflowListResponse(BaseModel):
    """Response body for listing workflows."""

    workflows: list[WorkflowResponse]
    total: int