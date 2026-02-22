/**
 * DAG (Directed Acyclic Graph) utilities.
 *
 * Provides cycle detection to ensure workflows are valid DAGs.
 * A DAG guarantees that execution always terminates and that
 * topological sort produces a deterministic execution order.
 */

import type { Edge } from "reactflow";

/**
 * Check if adding a new edge would create a cycle in the graph.
 * Uses DFS (Depth-First Search) to detect back edges.
 *
 * @param edges - Current edges in the graph.
 * @param newSource - Source node ID of the proposed edge.
 * @param newTarget - Target node ID of the proposed edge.
 * @returns True if the new edge would create a cycle.
 */
export function wouldCreateCycle(
  edges: Edge[],
  newSource: string,
  newTarget: string,
): boolean {
  // Self-loop is always a cycle
  if (newSource === newTarget) return true;

  // Build adjacency list including the proposed new edge
  const adjacency = new Map<string, string[]>();

  for (const edge of edges) {
    const neighbors = adjacency.get(edge.source) ?? [];
    neighbors.push(edge.target);
    adjacency.set(edge.source, neighbors);
  }

  // Add the proposed edge
  const sourceNeighbors = adjacency.get(newSource) ?? [];
  sourceNeighbors.push(newTarget);
  adjacency.set(newSource, sourceNeighbors);

  // DFS from newTarget to see if we can reach newSource (cycle)
  const visited = new Set<string>();
  const stack = [newTarget];

  while (stack.length > 0) {
    const node = stack.pop()!;
    if (node === newSource) return true;
    if (visited.has(node)) continue;
    visited.add(node);

    const neighbors = adjacency.get(node) ?? [];
    for (const neighbor of neighbors) {
      if (!visited.has(neighbor)) {
        stack.push(neighbor);
      }
    }
  }

  return false;
}