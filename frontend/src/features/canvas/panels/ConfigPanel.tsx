/**
 * Agent configuration panel.
 *
 * Appears on the right when an agent node is selected.
 * Allows editing: label, system prompt, provider, model,
 * temperature, and max tokens.
 */

import { X, Trash2 } from "lucide-react";
import { useWorkflowStore } from "../../../stores/workflowStore";
import type { AgentNodeData, ProviderType } from "../../../types/agent";
import { PROVIDER_MODELS, AGENT_TYPE_DEFAULTS } from "../../../types/agent";

export function ConfigPanel() {
  const selectedNodeId = useWorkflowStore((s) => s.selectedNodeId);
  const nodes = useWorkflowStore((s) => s.nodes);
  const updateNodeData = useWorkflowStore((s) => s.updateNodeData);
  const removeNode = useWorkflowStore((s) => s.removeNode);
  const selectNode = useWorkflowStore((s) => s.selectNode);

  const selectedNode = nodes.find((n) => n.id === selectedNodeId);

  if (!selectedNode || selectedNode.type !== "agent") return null;

  const data = selectedNode.data as AgentNodeData;

  const handleProviderChange = (provider: ProviderType) => {
    const models = PROVIDER_MODELS[provider]?.models ?? [];
    updateNodeData(selectedNode.id, {
      provider,
      model: models[0] ?? "",
    });
  };

  const handleDelete = () => {
    removeNode(selectedNode.id);
    selectNode(null);
  };

  return (
    <div className="w-80 border-l border-white/10 bg-[#0a0a0f] flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/10">
        <h2 className="text-sm font-semibold text-white">Configure Agent</h2>
        <button
          onClick={() => selectNode(null)}
          className="text-white/40 hover:text-white/70 transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Form */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Label */}
        <Field label="Name">
          <input
            type="text"
            value={data.label}
            onChange={(e) =>
              updateNodeData(selectedNode.id, { label: e.target.value })
            }
            className="w-full bg-white/5 border border-white/10 rounded-md px-3 py-1.5 
                       text-sm text-white placeholder-white/30 focus:outline-none 
                       focus:border-indigo-400 transition-colors"
          />
        </Field>

        {/* Agent Type (read-only badge) */}
        <Field label="Type">
          <div className="text-sm text-white/70">
            {AGENT_TYPE_DEFAULTS[data.agentType]?.emoji}{" "}
            {AGENT_TYPE_DEFAULTS[data.agentType]?.label}
          </div>
        </Field>

        {/* Provider */}
        <Field label="Provider">
          <select
            value={data.provider}
            onChange={(e) =>
              handleProviderChange(e.target.value as ProviderType)
            }
            className="w-full bg-white/5 border border-white/10 rounded-md px-3 py-1.5 
                       text-sm text-white focus:outline-none focus:border-indigo-400 
                       transition-colors"
          >
            {Object.entries(PROVIDER_MODELS).map(([key, val]) => (
              <option key={key} value={key} className="bg-[#1a1a2e]">
                {val.name}
              </option>
            ))}
          </select>
        </Field>

        {/* Model */}
        <Field label="Model">
          {PROVIDER_MODELS[data.provider]?.models.length > 0 ? (
            <select
              value={data.model}
              onChange={(e) =>
                updateNodeData(selectedNode.id, { model: e.target.value })
              }
              className="w-full bg-white/5 border border-white/10 rounded-md px-3 py-1.5 
                         text-sm text-white focus:outline-none focus:border-indigo-400 
                         transition-colors"
            >
              {PROVIDER_MODELS[data.provider].models.map((model) => (
                <option key={model} value={model} className="bg-[#1a1a2e]">
                  {model}
                </option>
              ))}
            </select>
          ) : (
            <input
              type="text"
              value={data.model}
              onChange={(e) =>
                updateNodeData(selectedNode.id, { model: e.target.value })
              }
              placeholder="Enter model name"
              className="w-full bg-white/5 border border-white/10 rounded-md px-3 py-1.5 
                         text-sm text-white placeholder-white/30 focus:outline-none 
                         focus:border-indigo-400 transition-colors"
            />
          )}
        </Field>

        {/* System Prompt */}
        <Field label="System Prompt">
          <textarea
            value={data.systemPrompt}
            onChange={(e) =>
              updateNodeData(selectedNode.id, {
                systemPrompt: e.target.value,
              })
            }
            rows={6}
            placeholder="Enter the agent's system prompt..."
            className="w-full bg-white/5 border border-white/10 rounded-md px-3 py-1.5 
                       text-sm text-white placeholder-white/30 focus:outline-none 
                       focus:border-indigo-400 transition-colors resize-y leading-relaxed"
          />
        </Field>

        {/* Temperature */}
        <Field label={`Temperature: ${data.temperature.toFixed(1)}`}>
          <input
            type="range"
            min="0"
            max="2"
            step="0.1"
            value={data.temperature}
            onChange={(e) =>
              updateNodeData(selectedNode.id, {
                temperature: parseFloat(e.target.value),
              })
            }
            className="w-full accent-indigo-400"
          />
          <div className="flex justify-between text-[10px] text-white/30 mt-0.5">
            <span>Precise</span>
            <span>Creative</span>
          </div>
        </Field>

        {/* Max Tokens */}
        <Field label="Max Tokens">
          <input
            type="number"
            value={data.maxTokens}
            onChange={(e) =>
              updateNodeData(selectedNode.id, {
                maxTokens: parseInt(e.target.value, 10) || 2048,
              })
            }
            min={1}
            max={128000}
            className="w-full bg-white/5 border border-white/10 rounded-md px-3 py-1.5 
                       text-sm text-white focus:outline-none focus:border-indigo-400 
                       transition-colors"
          />
        </Field>
      </div>

      {/* Footer — Delete */}
      <div className="px-4 py-3 border-t border-white/10">
        <button
          onClick={handleDelete}
          className="flex items-center gap-2 text-sm text-red-400 hover:text-red-300 
                     transition-colors"
        >
          <Trash2 className="w-3.5 h-3.5" />
          Delete Agent
        </button>
      </div>
    </div>
  );
}

/** Reusable form field wrapper. */
function Field({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="block text-xs font-medium text-white/50 mb-1.5">
        {label}
      </label>
      {children}
    </div>
  );
}