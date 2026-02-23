/**
 * Execution panel — displays real-time streaming output.
 *
 * Shows each agent's status, streaming text, token count,
 * and latency. Appears at the bottom of the screen during
 * workflow execution.
 */

import { useState } from "react";
import { ChevronDown, ChevronUp, X, Loader2, Check, AlertCircle, SkipForward } from "lucide-react";
import { useExecutionStore, type AgentRun, type AgentRunStatus } from "../../stores/executionStore";
import { useWorkflowStore } from "../../stores/workflowStore";

function StatusIcon({ status }: { status: AgentRunStatus }) {
  switch (status) {
    case "running":
      return <Loader2 className="w-3.5 h-3.5 text-indigo-400 animate-spin" />;
    case "completed":
      return <Check className="w-3.5 h-3.5 text-green-400" />;
    case "failed":
      return <AlertCircle className="w-3.5 h-3.5 text-red-400" />;
    case "skipped":
      return <SkipForward className="w-3.5 h-3.5 text-white/30" />;
    default:
      return <div className="w-3.5 h-3.5 rounded-full bg-white/10" />;
  }
}

function AgentRunCard({ run }: { run: AgentRun }) {
  const [expanded, setExpanded] = useState(run.status === "running");
  const nodes = useWorkflowStore((s) => s.nodes);
  const node = nodes.find((n) => n.id === run.agentId);
  const label = node?.data?.label ?? run.agentId;

  // Auto-expand when agent starts running
  if (run.status === "running" && !expanded) {
    setExpanded(true);
  }

  return (
    <div className="border border-white/5 rounded-lg bg-white/[0.02] overflow-hidden">
      {/* Header */}
      <button
        className="flex items-center justify-between w-full px-3 py-2 hover:bg-white/[0.03] transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-2">
          <StatusIcon status={run.status} />
          <span className="text-sm text-white/80">{label}</span>
        </div>
        <div className="flex items-center gap-3">
          {run.status === "completed" && (
            <span className="text-[11px] text-white/30">
              {run.tokensUsed} tokens · {(run.latencyMs / 1000).toFixed(1)}s
            </span>
          )}
          {expanded ? (
            <ChevronUp className="w-3.5 h-3.5 text-white/30" />
          ) : (
            <ChevronDown className="w-3.5 h-3.5 text-white/30" />
          )}
        </div>
      </button>

      {/* Output */}
      {expanded && (
        <div className="px-3 pb-3">
          <div className="bg-black/30 rounded-md p-3 text-sm text-white/70 leading-relaxed max-h-48 overflow-y-auto whitespace-pre-wrap font-mono text-xs">
            {run.output || (
              <span className="text-white/20 italic">
                {run.status === "running" ? "Generating..." : "No output"}
              </span>
            )}
            {run.status === "running" && (
              <span className="inline-block w-1.5 h-4 bg-indigo-400 animate-pulse ml-0.5" />
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export function ExecutionPanel() {
  const workflowStatus = useExecutionStore((s) => s.workflowStatus);
  const agentRuns = useExecutionStore((s) => s.agentRuns);
  const totalTokens = useExecutionStore((s) => s.totalTokens);
  const reset = useExecutionStore((s) => s.reset);

  if (workflowStatus === "idle") return null;

  const runs = Object.values(agentRuns).filter((r) => r.status !== "skipped");

  return (
    <div className="border-t border-white/10 bg-[#0a0a0f]">
      {/* Panel Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-white/5">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-medium text-white/70">Execution</h3>
          {workflowStatus === "running" && (
            <Loader2 className="w-3.5 h-3.5 text-indigo-400 animate-spin" />
          )}
          {workflowStatus === "completed" && (
            <span className="text-xs text-green-400">Completed · {totalTokens} tokens</span>
          )}
          {workflowStatus === "failed" && (
            <span className="text-xs text-red-400">Failed</span>
          )}
          {workflowStatus === "cancelled" && (
            <span className="text-xs text-amber-400">Cancelled</span>
          )}
        </div>
        {workflowStatus !== "running" && (
          <button
            onClick={reset}
            className="text-white/30 hover:text-white/60 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Agent Runs */}
      <div className="p-3 space-y-2 max-h-80 overflow-y-auto">
        {runs.map((run) => (
          <AgentRunCard key={run.agentId} run={run} />
        ))}
      </div>
    </div>
  );
}