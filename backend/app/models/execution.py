"""Workflow and agent execution ORM models.

Tracks the lifecycle of each workflow run (WorkflowExecution) and
the individual agent executions within it (AgentExecution).

State machines:
    WorkflowExecution: PENDING → RUNNING → COMPLETED | FAILED | CANCELLED
    AgentExecution:    IDLE → WAITING → RUNNING → COMPLETED | FAILED | SKIPPED
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ExecutionStatus(str, enum.Enum):
    """Workflow-level execution states."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentStatus(str, enum.Enum):
    """Individual agent execution states."""

    IDLE = "idle"
    WAITING = "waiting"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowExecution(Base):
    """A single run of a workflow.

    Created when the user clicks "Run". Transitions through
    PENDING → RUNNING → COMPLETED/FAILED/CANCELLED.
    """

    __tablename__ = "workflow_executions"

    workflow_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workflows.id", ondelete="CASCADE"),
    )
    status: Mapped[ExecutionStatus] = mapped_column(
        Enum(ExecutionStatus),
        default=ExecutionStatus.PENDING,
    )
    trigger_input: Mapped[dict] = mapped_column(JSON, default=dict)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    workflow: Mapped["Workflow"] = relationship(back_populates="executions")
    agent_executions: Mapped[list["AgentExecution"]] = relationship(
        back_populates="workflow_execution",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<WorkflowExecution id={self.id} status={self.status.value}>"


class AgentExecution(Base):
    """Execution record for a single agent within a workflow run.

    Tracks input/output data, token usage, and latency for
    each agent that runs during a workflow execution.
    """

    __tablename__ = "agent_executions"

    workflow_execution_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workflow_executions.id", ondelete="CASCADE"),
    )
    agent_node_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agent_nodes.id", ondelete="CASCADE"),
    )
    status: Mapped[AgentStatus] = mapped_column(
        Enum(AgentStatus),
        default=AgentStatus.IDLE,
    )
    input_data: Mapped[dict] = mapped_column(JSON, default=dict)
    output_data: Mapped[dict] = mapped_column(JSON, default=dict)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    # Relationships
    workflow_execution: Mapped["WorkflowExecution"] = relationship(
        back_populates="agent_executions",
    )

    def __repr__(self) -> str:
        return f"<AgentExecution id={self.id} agent={self.agent_node_id} status={self.status.value}>"