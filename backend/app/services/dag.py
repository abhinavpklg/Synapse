"""DAG (Directed Acyclic Graph) utilities for workflow execution.

Provides topological sorting to determine agent execution order
and cycle detection to validate workflow structure.

A valid workflow is a DAG — no cycles, guaranteed termination.
Topological sort produces a linear ordering where every agent
runs after all its dependencies have completed.
"""

from collections import defaultdict, deque

from app.core.exceptions import ValidationError
from app.core.logging import get_logger

logger = get_logger(__name__)


def topological_sort(
    nodes: list[dict],
    edges: list[dict],
) -> list[str]:
    """Compute execution order via Kahn's algorithm (BFS topological sort).

    Kahn's algorithm works by:
    1. Find all nodes with no incoming edges (in-degree 0) — these run first
    2. Process them, removing their outgoing edges
    3. Any newly exposed nodes (in-degree drops to 0) get added to the queue
    4. If all nodes are processed, the graph is a valid DAG

    Args:
        nodes: List of node dicts, each with an "id" field.
        edges: List of edge dicts, each with "source" and "target" fields.

    Returns:
        List of node IDs in execution order.

    Raises:
        ValidationError: If the graph contains a cycle.
    """
    node_ids = {node["id"] for node in nodes}

    # Build adjacency list and in-degree count
    adjacency: dict[str, list[str]] = defaultdict(list)
    in_degree: dict[str, int] = {node_id: 0 for node_id in node_ids}

    for edge in edges:
        source = edge["source"]
        target = edge["target"]
        if source in node_ids and target in node_ids:
            adjacency[source].append(target)
            in_degree[target] = in_degree.get(target, 0) + 1

    # Start with all nodes that have no dependencies (in-degree 0)
    queue: deque[str] = deque()
    for node_id in node_ids:
        if in_degree[node_id] == 0:
            queue.append(node_id)

    execution_order: list[str] = []

    while queue:
        node_id = queue.popleft()
        execution_order.append(node_id)

        for neighbor in adjacency[node_id]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    # If we didn't process all nodes, there's a cycle
    if len(execution_order) != len(node_ids):
        processed = set(execution_order)
        cycle_nodes = node_ids - processed
        raise ValidationError(
            f"Workflow contains a cycle involving nodes: {cycle_nodes}"
        )

    logger.debug("topological_sort_complete", order=execution_order)
    return execution_order


def get_node_dependencies(
    node_id: str,
    edges: list[dict],
) -> list[str]:
    """Get the IDs of all nodes that feed into the given node.

    Args:
        node_id: The target node.
        edges: All edges in the workflow.

    Returns:
        List of source node IDs that connect to this node.
    """
    return [edge["source"] for edge in edges if edge["target"] == node_id]