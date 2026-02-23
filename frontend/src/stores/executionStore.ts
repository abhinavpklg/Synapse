/**
 * Zustand store for workflow execution state.
 *
 * Tracks the current execution status, per-agent streaming output,
 * and provides actions to start/cancel execution and process
 * incoming WebSocket events.
 */

import { create } from "zustand";

/** Status of an individual agent during execution. */
export type AgentRunStatus =
  | "idle"
  | "waiting"
  | "running"
  | "completed"
  | "failed"
  | "skipped";

/** Streaming output for a single agent. */
export interface AgentRun {
  agentId: string;
  status: AgentRunStatus;
  output: string;
  tokensUsed: number;
  latencyMs: number;
}

interface ExecutionState {
  // ── State ─────────────────────────────────────────
  executionId: string | null;
  isRunning: boolean;
  workflowStatus: "idle" | "running" | "completed" | "failed" | "cancelled";
  agentRuns: Record<string, AgentRun>;
  totalTokens: number;

  // ── Actions ───────────────────────────────────────
  startExecution: (executionId: string, agentIds: string[]) => void;
  updateAgentStatus: (agentId: string, status: AgentRunStatus) => void;
  appendAgentOutput: (agentId: string, chunk: string) => void;
  completeAgent: (agentId: string, tokensUsed: number, latencyMs: number) => void;
  completeWorkflow: (status: "completed" | "failed" | "cancelled", totalTokens?: number) => void;
  reset: () => void;
}

export const useExecutionStore = create<ExecutionState>((set) => ({
  // ── Initial State ───────────────────────────────────
  executionId: null,
  isRunning: false,
  workflowStatus: "idle",
  agentRuns: {},
  totalTokens: 0,

  // ── Actions ─────────────────────────────────────────
  startExecution: (executionId, agentIds) => {
    const agentRuns: Record<string, AgentRun> = {};
    for (const id of agentIds) {
      agentRuns[id] = {
        agentId: id,
        status: "waiting",
        output: "",
        tokensUsed: 0,
        latencyMs: 0,
      };
    }
    set({
      executionId,
      isRunning: true,
      workflowStatus: "running",
      agentRuns,
      totalTokens: 0,
    });
  },

  updateAgentStatus: (agentId, status) => {
    set((state) => ({
      agentRuns: {
        ...state.agentRuns,
        [agentId]: {
          ...(state.agentRuns[agentId] ?? {
            agentId,
            output: "",
            tokensUsed: 0,
            latencyMs: 0,
          }),
          status,
        },
      },
    }));
  },

  appendAgentOutput: (agentId, chunk) => {
    set((state) => {
      const existing = state.agentRuns[agentId];
      if (!existing) return state;
      return {
        agentRuns: {
          ...state.agentRuns,
          [agentId]: {
            ...existing,
            output: existing.output + chunk,
          },
        },
      };
    });
  },

  completeAgent: (agentId, tokensUsed, latencyMs) => {
    set((state) => {
      const existing = state.agentRuns[agentId];
      if (!existing) return state;
      return {
        agentRuns: {
          ...state.agentRuns,
          [agentId]: {
            ...existing,
            status: "completed",
            tokensUsed,
            latencyMs,
          },
        },
      };
    });
  },

  completeWorkflow: (status, totalTokens) => {
    set({
      isRunning: false,
      workflowStatus: status,
      totalTokens: totalTokens ?? 0,
    });
  },

  reset: () => {
    set({
      executionId: null,
      isRunning: false,
      workflowStatus: "idle",
      agentRuns: {},
      totalTokens: 0,
    });
  },
}));