/**
 * Custom React Flow node for AI agents.
 *
 * Displays the agent's label, type badge, provider/model,
 * and execution status indicator. Border color changes based
 * on execution state (idle → running → completed/failed).
 */

import { memo } from "react";
import { Handle, Position, type NodeProps } from "reactflow";
import { Loader2 } from "lucide-react";
import type { AgentNodeData } from "../../../types/agent";
import { PROVIDER_MODELS } from "../../../types/agent";
import { useWorkflowStore } from "../../../stores/workflowStore";
import { useExecutionStore } from "../../../stores/executionStore";

/** Border color based on execution status. */
const STATUS_COLORS: Record<string, string> = {
  idle: "border-white/10",
  waiting: "border-white/10",
  running: "border-indigo-400 shadow-indigo-500/20",
  completed: "border-green-400 shadow-green-500/10",
  failed: "border-red-400 shadow-red-500/10",
  skipped: "border-white/5",
};

function AgentNodeComponent({ id, data, selected }: NodeProps<AgentNodeData>) {
  const selectNode = useWorkflowStore((s) => s.selectNode);
  const agentRun = useExecutionStore((s) => s.agentRuns[id]);
  const providerName = PROVIDER_MODELS[data.provider]?.name ?? data.provider;

  const runStatus = agentRun?.status ?? "idle";
  const isExecuting = runStatus === "running";

  // Use execution status color, or selection color if not executing
  const borderClass =
    runStatus !== "idle" && runStatus !== "waiting"
      ? STATUS_COLORS[runStatus]
      : selected
        ? "border-indigo-400 shadow-indigo-500/20"
        : "border-white/10 hover:border-white/20";

  return (
    <div
      className={`
        min-w-[180px] max-w-[220px] rounded-lg border bg-[#1a1a2e] px-3 py-2.5
        shadow-lg transition-all duration-300 cursor-pointer
        ${borderClass}
      `}
      onClick={() => selectNode(id)}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!w-2.5 !h-2.5 !bg-indigo-400 !border-2 !border-[#1a1a2e] !-top-1.5"
      />

      {/* Agent label + running indicator */}
      <div className="flex items-center gap-1.5">
        {isExecuting && (
          <Loader2 className="w-3.5 h-3.5 text-indigo-400 animate-spin shrink-0" />
        )}
        <div className="text-sm font-medium text-white truncate">
          {data.label}
        </div>
      </div>

      <div className="mt-1.5 flex items-center gap-1.5">
        <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 font-medium">
          {data.agentType}
        </span>
      </div>

      <div className="mt-1.5 text-[11px] text-white/40 truncate">
        {providerName} · {data.model}
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        className="!w-2.5 !h-2.5 !bg-indigo-400 !border-2 !border-[#1a1a2e] !-bottom-1.5"
      />
    </div>
  );
}

export const AgentNode = memo(AgentNodeComponent);