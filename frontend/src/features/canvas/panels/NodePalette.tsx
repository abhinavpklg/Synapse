/**
 * Sidebar palette for dragging agent nodes onto the canvas.
 *
 * Each palette item is draggable. When dropped on the React Flow
 * canvas, the onDrop handler in the parent reads the agent type
 * from the drag data and creates a new node at the drop position.
 */

import type { AgentType } from "../../../types/agent";
import { AGENT_TYPE_DEFAULTS } from "../../../types/agent";

/** Agent types available in the palette (input node is separate). */
const PALETTE_AGENT_TYPES: AgentType[] = [
  "researcher",
  "writer",
  "critic",
  "editor",
  "coder",
  "summarizer",
  "custom",
];

interface PaletteItemProps {
  agentType: AgentType;
}

function PaletteItem({ agentType }: PaletteItemProps) {
  const defaults = AGENT_TYPE_DEFAULTS[agentType];

  const onDragStart = (event: React.DragEvent) => {
    // Store the agent type in the drag data so the drop handler knows what to create
    event.dataTransfer.setData("application/synapse-agent-type", agentType);
    event.dataTransfer.effectAllowed = "move";
  };

  return (
    <div
      className="flex items-center gap-2.5 rounded-lg border border-white/5 bg-white/[0.03] 
                 px-3 py-2 cursor-grab active:cursor-grabbing hover:bg-white/[0.06] 
                 hover:border-white/10 transition-colors"
      draggable
      onDragStart={onDragStart}
    >
      <span className="text-base">{defaults.emoji}</span>
      <div className="min-w-0">
        <div className="text-sm font-medium text-white/90 truncate">
          {defaults.label}
        </div>
        <div className="text-[11px] text-white/40 truncate">
          {defaults.description}
        </div>
      </div>
    </div>
  );
}

function InputPaletteItem() {
  const onDragStart = (event: React.DragEvent) => {
    event.dataTransfer.setData("application/synapse-agent-type", "__input__");
    event.dataTransfer.effectAllowed = "move";
  };

  return (
    <div
      className="flex items-center gap-2.5 rounded-lg border border-emerald-500/20 
                 bg-emerald-500/[0.05] px-3 py-2 cursor-grab active:cursor-grabbing 
                 hover:bg-emerald-500/[0.1] transition-colors"
      draggable
      onDragStart={onDragStart}
    >
      <span className="text-base">📥</span>
      <div className="min-w-0">
        <div className="text-sm font-medium text-white/90">User Input</div>
        <div className="text-[11px] text-white/40">Workflow entry point</div>
      </div>
    </div>
  );
}

export function NodePalette() {
  return (
    <div className="w-56 border-r border-white/10 bg-[#0a0a0f] p-3 flex flex-col gap-1.5 overflow-y-auto">
      <h2 className="text-xs font-semibold text-white/50 uppercase tracking-wider mb-1 px-1">
        Nodes
      </h2>

      <InputPaletteItem />

      <div className="h-px bg-white/5 my-2" />

      <h2 className="text-xs font-semibold text-white/50 uppercase tracking-wider mb-1 px-1">
        Agents
      </h2>

      {PALETTE_AGENT_TYPES.map((agentType) => (
        <PaletteItem key={agentType} agentType={agentType} />
      ))}
    </div>
  );
}