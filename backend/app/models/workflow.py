"""Workflow, AgentNode, and Edge ORM models.

A Workflow contains the full React Flow canvas state (nodes + edges)
serialized as JSON, plus individual AgentNode and Edge records for
server-side querying and execution.
"""

import enum
import uuid

from sqlalchemy import (
    JSON,
    Boolean,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class AgentType(str, enum.Enum):
    """Pre-built agent type presets."""

    RESEARCHER = "researcher"
    WRITER = "writer"
    CRITIC = "critic"
    EDITOR = "editor"
    CODER = "coder"
    SUMMARIZER = "summarizer"
    CUSTOM = "custom"


class ProviderType(str, enum.Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    GROQ = "groq"
    DEEPSEEK = "deepseek"
    OPENROUTER = "openrouter"
    CUSTOM = "custom"


class Workflow(Base):
    """A visual agent workflow (the canvas + metadata).

    The canvas_data field stores the complete React Flow state,
    including node positions, edge connections, and viewport.
    AgentNode and Edge records provide a relational view of the
    same data for execution and querying.
    """

    __tablename__ = "workflows"

    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    canvas_data: Mapped[dict] = mapped_column(JSON, default=dict)
    is_template: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    agent_nodes: Mapped[list["AgentNode"]] = relationship(
        back_populates="workflow",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    edges: Mapped[list["Edge"]] = relationship(
        back_populates="workflow",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    executions: Mapped[list["WorkflowExecution"]] = relationship(
        back_populates="workflow",
        cascade="all, delete-orphan",
        lazy="noload",
    )

    def __repr__(self) -> str:
        return f"<Workflow id={self.id} name='{self.name}'>"


class AgentNode(Base):
    """An individual agent node within a workflow.

    Each node has a role (type), system prompt, LLM provider/model
    configuration, and optional MCP server connections for tool access.
    """

    __tablename__ = "agent_nodes"

    workflow_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workflows.id", ondelete="CASCADE"),
    )
    agent_type: Mapped[AgentType] = mapped_column(
        Enum(AgentType), default=AgentType.CUSTOM,
    )
    label: Mapped[str] = mapped_column(String(255), default="Agent")
    system_prompt: Mapped[str] = mapped_column(Text, default="")
    provider: Mapped[ProviderType] = mapped_column(
        Enum(ProviderType), default=ProviderType.OPENAI,
    )
    model: Mapped[str] = mapped_column(String(255), default="gpt-4o")
    temperature: Mapped[float] = mapped_column(Float, default=0.7)
    max_tokens: Mapped[int] = mapped_column(Integer, default=2048)
    mcp_servers: Mapped[list] = mapped_column(JSON, default=list)
    position_x: Mapped[float] = mapped_column(Float, default=0.0)
    position_y: Mapped[float] = mapped_column(Float, default=0.0)
    input_mapping: Mapped[dict] = mapped_column(JSON, default=dict)

    # Relationships
    workflow: Mapped["Workflow"] = relationship(back_populates="agent_nodes")

    def __repr__(self) -> str:
        return f"<AgentNode id={self.id} label='{self.label}' type={self.agent_type.value}>"


class Edge(Base):
    """A directional connection between two agent nodes.

    Edges define data flow: the source node's output feeds into
    the target node's input. Optional conditions enable branching.
    """

    __tablename__ = "edges"

    workflow_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workflows.id", ondelete="CASCADE"),
    )
    source_node_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agent_nodes.id", ondelete="CASCADE"),
    )
    target_node_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agent_nodes.id", ondelete="CASCADE"),
    )
    condition: Mapped[str | None] = mapped_column(String(500), nullable=True)
    data_key: Mapped[str] = mapped_column(String(255), default="output")

    # Relationships
    workflow: Mapped["Workflow"] = relationship(back_populates="edges")

    def __repr__(self) -> str:
        return f"<Edge {self.source_node_id} → {self.target_node_id}>"