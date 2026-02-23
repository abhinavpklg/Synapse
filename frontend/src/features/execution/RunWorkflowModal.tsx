/**
 * Modal for starting a workflow execution.
 *
 * Collects the user's initial input and optional API keys,
 * then triggers the execution.
 */

import { useState } from "react";
import { X, Play } from "lucide-react";
import { api } from "../../services/api";
import { useWorkflowStore } from "../../stores/workflowStore";
import { useExecutionStore } from "../../stores/executionStore";

interface RunWorkflowModalProps {
  onClose: () => void;
}

export function RunWorkflowModal({ onClose }: RunWorkflowModalProps) {
  const [input, setInput] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const workflowId = useWorkflowStore((s) => s.workflowId);
  const workflowName = useWorkflowStore((s) => s.workflowName);
  const nodes = useWorkflowStore((s) => s.nodes);
  const saveWorkflow = useWorkflowStore((s) => s.saveWorkflow);
  const startExecution = useExecutionStore((s) => s.startExecution);

  const handleRun = async () => {
    if (!input.trim()) {
      setError("Please provide input for the workflow");
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      // Save workflow first if needed
      let currentWorkflowId = workflowId;
      if (!currentWorkflowId) {
        await saveWorkflow();
        currentWorkflowId = useWorkflowStore.getState().workflowId;
      }

      if (!currentWorkflowId) {
        setError("Failed to save workflow");
        return;
      }

      // Start execution
      const response = await api.post(
        `/executions/workflows/${currentWorkflowId}/execute`,
        {
          trigger_input: { input: input.trim() },
          api_keys: {}, // Keys come from backend .env
        },
      );

      const executionId = response.data.id;
      const agentIds = nodes.map((n) => n.id);
      startExecution(executionId, agentIds);
      onClose();
    } catch (err) {
      console.error("Failed to start execution:", err);
      setError("Failed to start execution. Check the console for details.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <div className="bg-[#1a1a2e] border border-white/10 rounded-xl w-full max-w-lg mx-4 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-white/5">
          <div>
            <h2 className="text-base font-semibold text-white">Run Workflow</h2>
            <p className="text-xs text-white/40 mt-0.5">{workflowName}</p>
          </div>
          <button
            onClick={onClose}
            className="text-white/40 hover:text-white/70 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-5 space-y-4">
          <div>
            <label className="block text-sm font-medium text-white/60 mb-2">
              Input
            </label>
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              rows={4}
              placeholder="e.g., Write a comprehensive article about quantum computing breakthroughs in 2025..."
              className="w-full bg-black/30 border border-white/10 rounded-lg px-4 py-3 
                         text-sm text-white placeholder-white/20 focus:outline-none 
                         focus:border-indigo-400 transition-colors resize-y leading-relaxed"
              autoFocus
            />
          </div>

          {error && (
            <p className="text-sm text-red-400">{error}</p>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 px-5 py-4 border-t border-white/5">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-white/50 hover:text-white/70 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleRun}
            disabled={isSubmitting}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium
                       bg-indigo-500 text-white hover:bg-indigo-400 transition-colors
                       disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Play className="w-4 h-4" />
            {isSubmitting ? "Starting..." : "Run"}
          </button>
        </div>
      </div>
    </div>
  );
}