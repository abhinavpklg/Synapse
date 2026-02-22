/**
 * Zustand store for workflow canvas state.
 *
 * Manages all React Flow nodes, edges, and the currently selected
 * node. Provides actions for adding/removing/updating nodes,
 * connecting edges (with cycle detection), and serializing
 * the canvas for API persistence.
 */

import { create } from "zustand";
import {
  type Node,
  type Edge,
  type OnNodesChange,
  type OnEdgesChange,
  type Connection,
  applyNodeChanges,
  applyEdgeChanges,
  addEdge,
} from "reactflow";
import type { AgentNodeData, AgentType } from "../types/agent";
import { AGENT_TYPE_DEFAULTS } from "../types/agent";
import type { InputNodeData } from "../types/workflow";
import { wouldCreateCycle } from "../lib/dag";
import { createWorkflow, getWorkflow, updateWorkflow } from "../services/workflowService";

/** Default edge style for the canvas. */
const DEFAULT_EDGE_STYLE = {
  stroke: "#6366f1",
  strokeWidth: 2,
};

/** Create default AgentNodeData for a given agent type. */
function createAgentData(agentType: AgentType): AgentNodeData {
  const defaults = AGENT_TYPE_DEFAULTS[agentType];
  return {
    label: defaults.label,
    agentType,
    systemPrompt: defaults.systemPrompt,
    provider: "openai",
    model: "gpt-4o",
    temperature: 0.7,
    maxTokens: 2048,
    mcpServers: [],
    inputMapping: {},
  };
}

/** Workflow store state shape. */
interface WorkflowState {
  // ── State ─────────────────────────────────────────
  workflowId: string | null;
  workflowName: string;
  nodes: Node[];
  edges: Edge[];
  selectedNodeId: string | null;
  hasUnsavedChanges: boolean;

  // ── React Flow Callbacks ──────────────────────────
  onNodesChange: OnNodesChange;
  onEdgesChange: OnEdgesChange;
  onConnect: (connection: Connection) => void;

  // ── Node Actions ──────────────────────────────────
  addAgentNode: (agentType: AgentType, position: { x: number; y: number }) => void;
  addInputNode: (position: { x: number; y: number }) => void;
  removeNode: (nodeId: string) => void;
  updateNodeData: (nodeId: string, data: Partial<AgentNodeData>) => void;
  selectNode: (nodeId: string | null) => void;

  // ── Workflow Actions ──────────────────────────────
  setWorkflow: (id: string | null, name: string, nodes: Node[], edges: Edge[]) => void;
  setWorkflowName: (name: string) => void;
  clearCanvas: () => void;
  getCanvasData: () => { nodes: Node[]; edges: Edge[] };
  saveWorkflow: () => Promise<void>;
  loadWorkflow: (id: string) => Promise<void>;
  isSaving: boolean;
}

/** Input node that serves as the workflow entry point. */
function createInputNode(position: { x: number; y: number }): Node<InputNodeData> {
  return {
    id: `input-${Date.now()}`,
    type: "inputNode",
    position,
    data: {
      label: "User Input",
      description: "Starting input for the workflow",
    },
  };
}

export const useWorkflowStore = create<WorkflowState>((set, get) => ({
  // ── Initial State ───────────────────────────────────
  workflowId: null,
  workflowName: "Untitled Workflow",
  nodes: [],
  edges: [],
  selectedNodeId: null,
  hasUnsavedChanges: false,
  isSaving: false,

  // ── React Flow Callbacks ────────────────────────────
  onNodesChange: (changes) => {
    set((state) => ({
      nodes: applyNodeChanges(changes, state.nodes),
      hasUnsavedChanges: true,
    }));
  },

  onEdgesChange: (changes) => {
    set((state) => ({
      edges: applyEdgeChanges(changes, state.edges),
      hasUnsavedChanges: true,
    }));
  },

  onConnect: (connection: Connection) => {
    if (!connection.source || !connection.target) return;

    const { edges } = get();

    // Prevent cycles
    if (wouldCreateCycle(edges, connection.source, connection.target)) {
      console.warn("Connection rejected: would create a cycle");
      return;
    }

    set((state) => ({
      edges: addEdge(
        {
          ...connection,
          animated: true,
          style: DEFAULT_EDGE_STYLE,
        },
        state.edges,
      ),
      hasUnsavedChanges: true,
    }));
  },

  // ── Node Actions ────────────────────────────────────
  addAgentNode: (agentType, position) => {
    const nodeId = `agent-${Date.now()}`;
    const data = createAgentData(agentType);
    const defaults = AGENT_TYPE_DEFAULTS[agentType];

    const newNode: Node<AgentNodeData> = {
      id: nodeId,
      type: "agent",
      position,
      data: { ...data, label: `${defaults.emoji} ${defaults.label}` },
    };

    set((state) => ({
      nodes: [...state.nodes, newNode],
      hasUnsavedChanges: true,
    }));
  },

  addInputNode: (position) => {
    // Only allow one input node
    const { nodes } = get();
    const hasInput = nodes.some((n) => n.type === "inputNode");
    if (hasInput) {
      console.warn("Only one input node is allowed per workflow");
      return;
    }

    set((state) => ({
      nodes: [...state.nodes, createInputNode(position)],
      hasUnsavedChanges: true,
    }));
  },

  removeNode: (nodeId) => {
    set((state) => ({
      nodes: state.nodes.filter((n) => n.id !== nodeId),
      edges: state.edges.filter(
        (e) => e.source !== nodeId && e.target !== nodeId,
      ),
      selectedNodeId:
        state.selectedNodeId === nodeId ? null : state.selectedNodeId,
      hasUnsavedChanges: true,
    }));
  },

  updateNodeData: (nodeId, data) => {
    set((state) => ({
      nodes: state.nodes.map((node) =>
        node.id === nodeId
          ? { ...node, data: { ...node.data, ...data } }
          : node,
      ),
      hasUnsavedChanges: true,
    }));
  },

  selectNode: (nodeId) => {
    set({ selectedNodeId: nodeId });
  },

  // ── Workflow Actions ────────────────────────────────
  setWorkflow: (id, name, nodes, edges) => {
    set({
      workflowId: id,
      workflowName: name,
      nodes,
      edges,
      selectedNodeId: null,
      hasUnsavedChanges: false,
    });
  },

  setWorkflowName: (name) => {
    set({ workflowName: name, hasUnsavedChanges: true });
  },

  clearCanvas: () => {
    set({
      workflowId: null,
      workflowName: "Untitled Workflow",
      nodes: [],
      edges: [],
      selectedNodeId: null,
      hasUnsavedChanges: false,
    });
  },

  getCanvasData: () => {
    const { nodes, edges } = get();
    return { nodes, edges };
  },

  saveWorkflow: async () => {
    const { workflowId, workflowName, nodes, edges } = get();
    set({ isSaving: true });

    try {
      if (workflowId) {
        // Update existing workflow
        await updateWorkflow(workflowId, {
          name: workflowName,
          canvas_data: { nodes, edges },
        });
      } else {
        // Create new workflow
        const created = await createWorkflow({
          name: workflowName,
          canvas_data: { nodes, edges },
        });
        set({ workflowId: created.id });
      }
      set({ hasUnsavedChanges: false });
    } catch (error) {
      console.error("Failed to save workflow:", error);
      throw error;
    } finally {
      set({ isSaving: false });
    }
  },

  loadWorkflow: async (id: string) => {
    try {
      const workflow = await getWorkflow(id);
      const canvasData = workflow.canvas_data ?? { nodes: [], edges: [] };
      set({
        workflowId: workflow.id,
        workflowName: workflow.name,
        nodes: canvasData.nodes ?? [],
        edges: (canvasData.edges ?? []).map((e: Record<string, unknown>) => ({
          ...e,
          animated: true,
          style: { stroke: "#6366f1", strokeWidth: 2 },
        })),
        selectedNodeId: null,
        hasUnsavedChanges: false,
      });
    } catch (error) {
      console.error("Failed to load workflow:", error);
      throw error;
    }
  },
}));