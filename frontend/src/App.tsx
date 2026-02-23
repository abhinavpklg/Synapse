import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  BackgroundVariant,
  type ReactFlowInstance,
} from "reactflow";
import "reactflow/dist/style.css";
import { Zap, Save, Play, StopCircle } from "lucide-react";

import { AgentNode } from "./features/canvas/nodes/AgentNode";
import { InputNode } from "./features/canvas/nodes/InputNode";
import { NodePalette } from "./features/canvas/panels/NodePalette";
import { ConfigPanel } from "./features/canvas/panels/ConfigPanel";
import { ExecutionPanel } from "./features/execution/ExecutionPanel";
import { RunWorkflowModal } from "./features/execution/RunWorkflowModal";
import { useExecutionWebSocket } from "./features/execution/hooks/useExecutionWebSocket";
import { useWorkflowStore } from "./stores/workflowStore";
import { useExecutionStore } from "./stores/executionStore";
import type { AgentType } from "./types/agent";

export default function App() {
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const [reactFlowInstance, setReactFlowInstance] =
    useState<ReactFlowInstance | null>(null);
  const [backendStatus, setBackendStatus] = useState<
    "checking" | "ok" | "error"
  >("checking");
  const [showRunModal, setShowRunModal] = useState(false);

  // ── Workflow store ────────────────────────────────
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
  const saveWorkflow = useWorkflowStore((s) => s.saveWorkflow);
  const isSaving = useWorkflowStore((s) => s.isSaving);

  // ── Execution store ───────────────────────────────
  const executionId = useExecutionStore((s) => s.executionId);
  const isRunning = useExecutionStore((s) => s.isRunning);

  // ── WebSocket hook ────────────────────────────────
  const { cancelExecution } = useExecutionWebSocket(executionId);

  // ── Custom node types ─────────────────────────────
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

  // ── Drag & Drop ───────────────────────────────────
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

  const onPaneClick = useCallback(() => {
    selectNode(null);
  }, [selectNode]);

  const onNodeClick = useCallback(
    (_event: React.MouseEvent, node: { id: string }) => {
      selectNode(node.id);
    },
    [selectNode],
  );

  const hasNodes = nodes.length > 0;

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

        <div className="flex items-center gap-2">
          {/* Run / Cancel button */}
          {isRunning ? (
            <button
              onClick={cancelExecution}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium
                         bg-red-500/20 text-red-300 border border-red-500/30 hover:bg-red-500/30
                         transition-colors"
            >
              <StopCircle className="w-3.5 h-3.5" />
              Cancel
            </button>
          ) : (
            <button
              onClick={() => setShowRunModal(true)}
              disabled={!hasNodes}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium
                         transition-colors border ${
                           hasNodes
                             ? "bg-green-500/20 text-green-300 border-green-500/30 hover:bg-green-500/30"
                             : "bg-white/5 text-white/30 border-white/10 cursor-default"
                         }`}
            >
              <Play className="w-3.5 h-3.5" />
              Run
            </button>
          )}

          {/* Save button */}
          <button
            onClick={() => saveWorkflow()}
            disabled={isSaving || !hasUnsavedChanges}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium
                       transition-colors border ${
                         hasUnsavedChanges
                           ? "bg-indigo-500/20 text-indigo-300 border-indigo-500/30 hover:bg-indigo-500/30"
                           : "bg-white/5 text-white/40 border-white/10 cursor-default"
                       }`}
          >
            <Save className="w-3.5 h-3.5" />
            {isSaving ? "Saving..." : "Save"}
          </button>

          {/* Backend status */}
          <div className="flex items-center gap-1.5 text-xs ml-1">
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

        {/* Center: Canvas + Execution Panel */}
        <div className="flex-1 flex flex-col">
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

          {/* Execution output panel */}
          <ExecutionPanel />
        </div>

        {/* Right: Config Panel */}
        {selectedNodeId && <ConfigPanel />}
      </div>

      {/* Run modal */}
      {showRunModal && (
        <RunWorkflowModal onClose={() => setShowRunModal(false)} />
      )}
    </div>
  );
}