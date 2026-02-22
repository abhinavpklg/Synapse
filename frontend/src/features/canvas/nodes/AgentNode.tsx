/**
 * Custom React Flow node for AI agents.
 *
 * Displays the agent's label, type badge, provider, and model.
 * Highlights when selected. Has input handle (top) and output
 * handle (bottom) for connecting to other nodes.
 */

import { memo } from "react";
import { Handle, Position, type NodeProps } from "reactflow";
import type { AgentNodeData } from "../../../types/agent";
import { PROVIDER_MODELS } from "../../../types/agent";
import { useWorkflowStore } from "../../../stores/workflowStore";

function AgentNodeComponent({ id, data, selected }: NodeProps<AgentNodeData>) {
  const selectNode = useWorkflowStore((s) => s.selectNode);
  const providerName = PROVIDER_MODELS[data.provider]?.name ?? data.provider;

  return (
    <div
      className={`
        min-w-[180px] max-w-[220px] rounded-lg border bg-[#1a1a2e] px-3 py-2.5
        shadow-lg transition-all duration-150 cursor-pointer
        ${selected ? "border-indigo-400 shadow-indigo-500/20" : "border-white/10 hover:border-white/20"}
      `}
      onClick={() => selectNode(id)}
    >
      {/* Input handle */}
      <Handle
        type="target"
        position={Position.Top}
        className="!w-2.5 !h-2.5 !bg-indigo-400 !border-2 !border-[#1a1a2e] !-top-1.5"
      />

      {/* Agent label */}
      <div className="text-sm font-medium text-white truncate">
        {data.label}
      </div>

      {/* Agent type badge + provider/model info */}
      <div className="mt-1.5 flex items-center gap-1.5">
        <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 font-medium">
          {data.agentType}
        </span>
      </div>

      <div className="mt-1.5 text-[11px] text-white/40 truncate">
        {providerName} · {data.model}
      </div>

      {/* Output handle */}
      <Handle
        type="source"
        position={Position.Bottom}
        className="!w-2.5 !h-2.5 !bg-indigo-400 !border-2 !border-[#1a1a2e] !-bottom-1.5"
      />
    </div>
  );
}

/** Memoized to prevent unnecessary re-renders on canvas interactions. */
export const AgentNode = memo(AgentNodeComponent);