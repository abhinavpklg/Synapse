import { useCallback, useState } from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  addEdge,
  useNodesState,
  useEdgesState,
  type Connection,
  type Node,
  type Edge,
  BackgroundVariant,
} from "reactflow";
import "reactflow/dist/style.css";
import { Zap } from "lucide-react";

/**
 * Demo nodes to verify React Flow renders correctly.
 * These will be replaced with dynamic nodes in M2.
 */
const initialNodes: Node[] = [
  {
    id: "input-1",
    type: "default",
    position: { x: 100, y: 200 },
    data: { label: "📥 User Input" },
    style: {
      background: "#1e1e2e",
      color: "#e2e8f0",
      border: "1px solid #6366f1",
      borderRadius: "8px",
      padding: "10px 16px",
      fontSize: "13px",
    },
  },
  {
    id: "agent-1",
    type: "default",
    position: { x: 400, y: 100 },
    data: { label: "🔍 Researcher" },
    style: {
      background: "#1e1e2e",
      color: "#e2e8f0",
      border: "1px solid #8b5cf6",
      borderRadius: "8px",
      padding: "10px 16px",
      fontSize: "13px",
    },
  },
  {
    id: "agent-2",
    type: "default",
    position: { x: 400, y: 300 },
    data: { label: "✍️ Writer" },
    style: {
      background: "#1e1e2e",
      color: "#e2e8f0",
      border: "1px solid #8b5cf6",
      borderRadius: "8px",
      padding: "10px 16px",
      fontSize: "13px",
    },
  },
  {
    id: "agent-3",
    type: "default",
    position: { x: 700, y: 200 },
    data: { label: "📝 Editor" },
    style: {
      background: "#1e1e2e",
      color: "#e2e8f0",
      border: "1px solid #8b5cf6",
      borderRadius: "8px",
      padding: "10px 16px",
      fontSize: "13px",
    },
  },
];

const initialEdges: Edge[] = [
  {
    id: "e-input-researcher",
    source: "input-1",
    target: "agent-1",
    animated: true,
    style: { stroke: "#6366f1" },
  },
  {
    id: "e-input-writer",
    source: "input-1",
    target: "agent-2",
    animated: true,
    style: { stroke: "#6366f1" },
  },
  {
    id: "e-researcher-editor",
    source: "agent-1",
    target: "agent-3",
    animated: true,
    style: { stroke: "#6366f1" },
  },
  {
    id: "e-writer-editor",
    source: "agent-2",
    target: "agent-3",
    animated: true,
    style: { stroke: "#6366f1" },
  },
];

export default function App() {
  const [nodes, , onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [backendStatus, setBackendStatus] = useState<
    "checking" | "ok" | "error"
  >("checking");

  // Check backend connectivity on mount
  useState(() => {
    fetch("/api/health")
      .then((res) => res.json())
      .then(() => setBackendStatus("ok"))
      .catch(() => setBackendStatus("error"));
  });

  const onConnect = useCallback(
    (connection: Connection) => {
      setEdges((eds) => addEdge({ ...connection, animated: true, style: { stroke: "#6366f1" } }, eds));
    },
    [setEdges]
  );

  return (
    <div className="flex flex-col h-screen bg-[#0a0a0f]">
      {/* ── Header ──────────────────────────────────── */}
      <header className="flex items-center justify-between px-4 py-2 border-b border-white/10 bg-[#0a0a0f]">
        <div className="flex items-center gap-2">
          <Zap className="w-5 h-5 text-indigo-400" />
          <h1 className="text-lg font-semibold text-white tracking-tight">
            Synapse
          </h1>
          <span className="text-xs text-white/40 ml-1">v0.1.0</span>
        </div>

        <div className="flex items-center gap-3">
          {/* Backend status indicator */}
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

      {/* ── Canvas ──────────────────────────────────── */}
      <div className="flex-1">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          fitView
          proOptions={{ hideAttribution: true }}
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
            nodeColor="#6366f1"
            maskColor="rgba(0, 0, 0, 0.7)"
          />
        </ReactFlow>
      </div>
    </div>
  );
}