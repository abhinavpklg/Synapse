/**
 * Custom React Flow node for workflow input.
 *
 * This is the entry point of every workflow — it provides the
 * initial user input that feeds into the first agent(s).
 * Only one input node is allowed per workflow.
 */

import { memo } from "react";
import { Handle, Position, type NodeProps } from "reactflow";
import type { InputNodeData } from "../../../types/workflow";

function InputNodeComponent({ data, selected }: NodeProps<InputNodeData>) {
  return (
    <div
      className={`
        min-w-[180px] max-w-[220px] rounded-lg border bg-[#1a1a2e] px-3 py-2.5
        shadow-lg transition-all duration-150
        ${selected ? "border-emerald-400 shadow-emerald-500/20" : "border-white/10 hover:border-white/20"}
      `}
    >
      {/* Label */}
      <div className="text-sm font-medium text-white">
        📥 {data.label}
      </div>

      <div className="mt-1 text-[11px] text-white/40">
        {data.description || "Starting input for the workflow"}
      </div>

      {/* Output handle only — input node has no inputs */}
      <Handle
        type="source"
        position={Position.Bottom}
        className="!w-2.5 !h-2.5 !bg-emerald-400 !border-2 !border-[#1a1a2e] !-bottom-1.5"
      />
    </div>
  );
}

export const InputNode = memo(InputNodeComponent);