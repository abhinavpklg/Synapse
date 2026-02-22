import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  BackgroundVariant,
  type ReactFlowInstance,
} from "reactflow";
import "reactflow/dist/style.css";
import { Zap, Save } from "lucide-react";

import { AgentNode } from "./features/canvas/nodes/AgentNode";
import { InputNode } from "./features/canvas/nodes/InputNode";
import { NodePalette } from "./features/canvas/panels/NodePalette";
import { ConfigPanel } from "./features/canvas/panels/ConfigPanel";
import { useWorkflowStore } from "./stores/workflowStore";
import type { AgentType } from "./types/agent";

/**
 * Root application component.
 *
 * Layout: [NodePalette] [ReactFlow Canvas] [ConfigPanel]
 * The palette is always visible. The config panel appears when
 * a node is selected.
 */
export default function App() {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [reactFlowInstance, setReactFlowInstance] =
    useState<ReactFlowInstance | null>(null);
  const [backendStatus, setBackendStatus] = useState<
    "checking" | "ok" | "error"
  >("checking");

  // ── Store bindings ────────────────────────────────
  const nodes = useWorkflowStore((s) => s.nodes);
  const edges = useWorkflowStore((s) => s.edges);
  const selectedNodeId = useWorkflowStore((s) => s.selectedNodeId);
  const onNodesChange = useWorkflowStore((s) => s.onNodesChange);
  const onEdgesChange = useWorkflowStore((s) => s.onEdgesChange);
  const onConnect = useWorkflowStore((s) => s.onConnect);
  const addAgentNode = useWorkflowStore((s) => s.addAgentNode);
  const addInputNode = useWorkflowStore((s) => s.addInputNode);
  const selectNode = useWorkflowStore((s) => s.selectNode);
  const workflowName = useWorkflowStore((s) => s.workflowName);
  const hasUnsavedChanges = useWorkflowStore((s) => s.hasUnsavedChanges);

  // ── Custom node types (memoized to avoid React Flow warning) ──
  const nodeTypes = useMemo(
    () => ({
      agent: AgentNode,
      inputNode: InputNode,
    }),
    [],
  );

  // ── Backend health check ──────────────────────────
  useEffect(() => {
    fetch("/api/health")
      .then((res) => res.json())
      .then(() => setBackendStatus("ok"))
      .catch(() => setBackendStatus("error"));
  }, []);

  // ── Drag & Drop handling ──────────────────────────
  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const agentType = event.dataTransfer.getData(
        "application/synapse-agent-type",
      );
      if (!agentType || !reactFlowInstance || !reactFlowWrapper.current) return;

      // Convert screen coordinates to canvas coordinates
      const bounds = reactFlowWrapper.current.getBoundingClientRect();
      const position = reactFlowInstance.screenToFlowPosition({
        x: event.clientX - bounds.left,
        y: event.clientY - bounds.top,
      });

      if (agentType === "__input__") {
        addInputNode(position);
      } else {
        addAgentNode(agentType as AgentType, position);
      }
    },
    [reactFlowInstance, addAgentNode, addInputNode],
  );

  // ── Deselect on canvas click ──────────────────────
  const onPaneClick = useCallback(() => {
    selectNode(null);
  }, [selectNode]);

  // ── Node click → select ───────────────────────────
  const onNodeClick = useCallback(
    (_event: React.MouseEvent, node: { id: string }) => {
      selectNode(node.id);
    },
    [selectNode],
  );

  return (
    <div className="flex flex-col h-screen bg-[#0a0a0f]">
      {/* ── Header ──────────────────────────────────── */}
      <header className="flex items-center justify-between px-4 py-2 border-b border-white/10 bg-[#0a0a0f] shrink-0">
        <div className="flex items-center gap-2">
          <Zap className="w-5 h-5 text-indigo-400" />
          <h1 className="text-lg font-semibold text-white tracking-tight">
            Synapse
          </h1>
          <span className="text-xs text-white/40 ml-1">v0.1.0</span>
          <span className="text-xs text-white/30 ml-3">
            {workflowName}
            {hasUnsavedChanges && (
              <span className="text-amber-400 ml-1">•</span>
            )}
          </span>
        </div>

        <div className="flex items-center gap-3">
          {/* Save button (wired in later) */}
          <button
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium
                       bg-white/5 text-white/60 hover:bg-white/10 hover:text-white 
                       transition-colors border border-white/10"
            title="Save workflow (coming soon)"
          >
            <Save className="w-3.5 h-3.5" />
            Save
          </button>

          {/* Backend status */}
          <div className="flex items-center gap-1.5 text-xs">
            <div
              className={`w-2 h-2 rounded-full ${
                backendStatus === "ok"
                  ? "bg-green-400"
                  : backendStatus === "error"
                    ? "bg-red-400"
                    : "bg-yellow-400 animate-pulse"
              }`}
            />
            <span className="text-white/50">
              {backendStatus === "ok"
                ? "API Connected"
                : backendStatus === "error"
                  ? "API Offline"
                  : "Connecting..."}
            </span>
          </div>
        </div>
      </header>

      {/* ── Main Layout ─────────────────────────────── */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left: Node Palette */}
        <NodePalette />

        {/* Center: Canvas */}
        <div className="flex-1" ref={reactFlowWrapper}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onInit={setReactFlowInstance}
            onDragOver={onDragOver}
            onDrop={onDrop}
            onPaneClick={onPaneClick}
            onNodeClick={onNodeClick}
            nodeTypes={nodeTypes}
            fitView
            proOptions={{ hideAttribution: true }}
            defaultEdgeOptions={{
              animated: true,
              style: { stroke: "#6366f1", strokeWidth: 2 },
            }}
          >
            <Background
              variant={BackgroundVariant.Dots}
              gap={20}
              size={1}
              color="#ffffff08"
            />
            <Controls
              style={{
                background: "#1e1e2e",
                borderColor: "#ffffff15",
                borderRadius: "8px",
              }}
            />
            <MiniMap
              style={{
                background: "#1e1e2e",
                borderColor: "#ffffff15",
                borderRadius: "8px",
              }}
              nodeColor={(node) =>
                node.type === "inputNode" ? "#10b981" : "#6366f1"
              }
              maskColor="rgba(0, 0, 0, 0.7)"
            />
          </ReactFlow>
        </div>

        {/* Right: Config Panel (visible when agent selected) */}
        {selectedNodeId && <ConfigPanel />}
      </div>
    </div>
  );
}