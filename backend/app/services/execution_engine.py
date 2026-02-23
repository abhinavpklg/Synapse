"""Workflow execution engine.

The core orchestrator that runs a workflow:
1. Topologically sorts agent nodes to determine execution order
2. For each agent: builds prompt, calls LLM provider, streams output
3. Broadcasts all events via Redis pub/sub for WebSocket delivery
4. Tracks execution state in the database

State machines:
    Workflow: PENDING → RUNNING → COMPLETED | FAILED | CANCELLED
    Agent:    IDLE → WAITING → RUNNING → COMPLETED | FAILED | SKIPPED
"""

import json
import time
from datetime import datetime, timezone

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ExecutionError, ProviderError
from app.core.logging import get_logger
from app.models.execution import (
    AgentExecution,
    AgentStatus,
    ExecutionStatus,
    WorkflowExecution,
)
from app.models.workflow import Workflow
from app.providers.base import LLMConfig, LLMMessage
from app.providers.registry import get_provider
from app.services.dag import get_node_dependencies, topological_sort

logger = get_logger(__name__)

# Redis key prefix for execution events
EXECUTION_CHANNEL_PREFIX = "execution:"

# Set of currently cancelled execution IDs (in-memory for this process)
_cancelled_executions: set[str] = set()


def cancel_execution(execution_id: str) -> None:
    """Mark an execution as cancelled (checked between agent runs)."""
    _cancelled_executions.add(execution_id)


def _is_cancelled(execution_id: str) -> bool:
    """Check if an execution has been cancelled."""
    return execution_id in _cancelled_executions


async def _publish_event(redis: Redis, execution_id: str, event: dict) -> None:
    """Publish an event to the execution's Redis channel.

    All WebSocket subscribers for this execution will receive it.
    """
    channel = f"{EXECUTION_CHANNEL_PREFIX}{execution_id}"
    event["timestamp"] = datetime.now(timezone.utc).isoformat()
    await redis.publish(channel, json.dumps(event))


async def run_workflow(
    db: AsyncSession,
    redis: Redis,
    workflow: Workflow,
    execution: WorkflowExecution,
    api_keys: dict[str, str],
) -> None:
    """Execute a workflow end-to-end.

    This is the main entry point called by the API layer.
    It runs in a background task so the HTTP response returns immediately.

    Args:
        db: Database session for persisting state.
        redis: Redis client for pub/sub broadcasting.
        workflow: The workflow to execute.
        execution: The WorkflowExecution record (already created).
        api_keys: Map of provider type → API key.
    """
    execution_id = str(execution.id)

    try:
        # Transition: PENDING → RUNNING
        execution.status = ExecutionStatus.RUNNING
        execution.started_at = datetime.now(timezone.utc)
        await db.flush()

        await _publish_event(redis, execution_id, {
            "type": "workflow_status",
            "status": "running",
        })

        canvas_data = workflow.canvas_data or {}
        nodes = canvas_data.get("nodes", [])
        edges = canvas_data.get("edges", [])

        if not nodes:
            raise ExecutionError("Workflow has no nodes to execute")

        # Topological sort → execution order
        execution_order = topological_sort(nodes, edges)
        node_map = {node["id"]: node for node in nodes}

        # Track outputs for passing between agents
        agent_outputs: dict[str, str] = {}

        # Create AgentExecution records for all nodes
        agent_executions: dict[str, AgentExecution] = {}
        for node_id in execution_order:
            agent_exec = AgentExecution(
                workflow_execution_id=execution.id,
                agent_node_id=node_id,
                status=AgentStatus.IDLE,
            )
            db.add(agent_exec)
            agent_executions[node_id] = agent_exec
        await db.flush()

        # Execute agents in order
        total_tokens = 0
        for node_id in execution_order:
            if _is_cancelled(execution_id):
                execution.status = ExecutionStatus.CANCELLED
                await _publish_event(redis, execution_id, {
                    "type": "workflow_completed",
                    "execution_id": execution_id,
                    "status": "cancelled",
                })
                break

            node = node_map[node_id]
            node_data = node.get("data", {})
            agent_exec = agent_executions[node_id]

            # Skip non-agent nodes (like inputNode)
            if node.get("type") != "agent":
                agent_exec.status = AgentStatus.SKIPPED
                # For input nodes, store the trigger input as their "output"
                trigger_text = execution.trigger_input.get("input", "")
                agent_outputs[node_id] = trigger_text
                await _publish_event(redis, execution_id, {
                    "type": "agent_status",
                    "agent_id": node_id,
                    "status": "skipped",
                })
                continue

            # Run this agent
            tokens = await _run_agent(
                db=db,
                redis=redis,
                execution_id=execution_id,
                node_id=node_id,
                node_data=node_data,
                agent_exec=agent_exec,
                edges=edges,
                agent_outputs=agent_outputs,
                api_keys=api_keys,
            )
            total_tokens += tokens

        # Workflow complete
        if execution.status != ExecutionStatus.CANCELLED:
            execution.status = ExecutionStatus.COMPLETED
            execution.completed_at = datetime.now(timezone.utc)
            await db.flush()

            await _publish_event(redis, execution_id, {
                "type": "workflow_completed",
                "execution_id": execution_id,
                "status": "completed",
                "total_tokens": total_tokens,
            })

    except Exception as exc:
        execution.status = ExecutionStatus.FAILED
        execution.error = str(exc)
        execution.completed_at = datetime.now(timezone.utc)
        await db.flush()

        await _publish_event(redis, execution_id, {
            "type": "error",
            "agent_id": None,
            "message": str(exc),
            "code": "EXECUTION_ERROR",
        })

        await _publish_event(redis, execution_id, {
            "type": "workflow_completed",
            "execution_id": execution_id,
            "status": "failed",
        })

        logger.error("workflow_execution_failed", execution_id=execution_id, error=str(exc))

    finally:
        _cancelled_executions.discard(execution_id)
        await db.commit()


async def _run_agent(
    *,
    db: AsyncSession,
    redis: Redis,
    execution_id: str,
    node_id: str,
    node_data: dict,
    agent_exec: AgentExecution,
    edges: list[dict],
    agent_outputs: dict[str, str],
    api_keys: dict[str, str],
) -> int:
    """Execute a single agent node.

    Builds the prompt from parent outputs, calls the LLM provider,
    streams output chunks, and records results.

    Returns:
        Number of tokens used by this agent.
    """
    # Transition: IDLE → RUNNING
    agent_exec.status = AgentStatus.RUNNING
    agent_exec.started_at = datetime.now(timezone.utc)
    await db.flush()

    await _publish_event(redis, execution_id, {
        "type": "agent_status",
        "agent_id": node_id,
        "status": "running",
    })

    start_time = time.monotonic()

    try:
        # Build input from parent node outputs
        parent_ids = get_node_dependencies(node_id, edges)
        parent_outputs = [
            agent_outputs[pid] for pid in parent_ids if pid in agent_outputs
        ]
        input_context = "\n\n---\n\n".join(parent_outputs) if parent_outputs else ""

        # Get provider and config
        provider_type = node_data.get("provider", "openai")
        api_key = api_keys.get(provider_type, "")
        provider = get_provider(provider_type, api_key)

        config = LLMConfig(
            model=node_data.get("model", "gpt-4o"),
            temperature=node_data.get("temperature", 0.7),
            max_tokens=node_data.get("maxTokens", 2048),
        )

        # Build messages
        messages: list[LLMMessage] = []
        system_prompt = node_data.get("systemPrompt", "")
        if system_prompt:
            messages.append(LLMMessage(role="system", content=system_prompt))

        user_content = input_context if input_context else "No input provided."
        messages.append(LLMMessage(role="user", content=user_content))

        # Store input data
        agent_exec.input_data = {"context": input_context, "system_prompt": system_prompt}

        # Stream response
        full_content = ""
        tokens_used = 0

        async for chunk in provider.stream(messages, config):
            if chunk.is_final:
                tokens_used = chunk.tokens_used
                break

            full_content += chunk.content
            await _publish_event(redis, execution_id, {
                "type": "agent_output_chunk",
                "agent_id": node_id,
                "chunk": chunk.content,
            })

        # Store output and transition: RUNNING → COMPLETED
        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        agent_outputs[node_id] = full_content

        agent_exec.status = AgentStatus.COMPLETED
        agent_exec.output_data = {"content": full_content}
        agent_exec.tokens_used = tokens_used
        agent_exec.latency_ms = elapsed_ms
        agent_exec.completed_at = datetime.now(timezone.utc)
        await db.flush()

        await _publish_event(redis, execution_id, {
            "type": "agent_completed",
            "agent_id": node_id,
            "output": full_content[:500],  # Truncated for the event
            "tokens_used": tokens_used,
            "latency_ms": elapsed_ms,
        })

        logger.info(
            "agent_completed",
            execution_id=execution_id,
            agent_id=node_id,
            tokens=tokens_used,
            latency_ms=elapsed_ms,
        )
        return tokens_used

    except ProviderError:
        raise
    except Exception as exc:
        agent_exec.status = AgentStatus.FAILED
        agent_exec.completed_at = datetime.now(timezone.utc)
        await db.flush()

        await _publish_event(redis, execution_id, {
            "type": "agent_status",
            "agent_id": node_id,
            "status": "failed",
        })

        raise ExecutionError(str(exc), agent_id=node_id) from exc