/**
 * Workflow type definitions.
 *
 * These types represent workflows as persisted in the database
 * and returned by the API. They mirror the backend Pydantic schemas.
 */

import type { AgentNodeData } from "./agent";

/** Workflow as returned by the API. */
export interface Workflow {
  id: string;
  name: string;
  description: string;
  canvas_data: CanvasData;
  is_template: boolean;
  created_at: string;
  updated_at: string;
}

/** Serialized React Flow canvas state. */
export interface CanvasData {
  nodes: CanvasNode[];
  edges: CanvasEdge[];
  viewport?: { x: number; y: number; zoom: number };
}

/** A node as serialized for the API (React Flow node shape). */
export interface CanvasNode {
  id: string;
  type: "agent" | "inputNode";
  position: { x: number; y: number };
  data: AgentNodeData | InputNodeData;
}

/** Data for the workflow input node. */
export interface InputNodeData {
  label: string;
  description: string;
}

/** An edge as serialized for the API. */
export interface CanvasEdge {
  id: string;
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
}

/** Payload for creating/updating a workflow. */
export interface WorkflowCreatePayload {
  name: string;
  description?: string;
  canvas_data: CanvasData;
}

export interface WorkflowUpdatePayload {
  name?: string;
  description?: string;
  canvas_data?: CanvasData;
}