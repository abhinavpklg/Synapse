/**
 * WebSocket hook for real-time execution streaming.
 *
 * Connects to the backend WebSocket, processes incoming events,
 * and updates the execution store. Automatically disconnects
 * when the workflow completes.
 */

import { useEffect, useRef } from "react";
import { useExecutionStore } from "../../../stores/executionStore";

export function useExecutionWebSocket(executionId: string | null) {
  const wsRef = useRef<WebSocket | null>(null);
  const updateAgentStatus = useExecutionStore((s) => s.updateAgentStatus);
  const appendAgentOutput = useExecutionStore((s) => s.appendAgentOutput);
  const completeAgent = useExecutionStore((s) => s.completeAgent);
  const completeWorkflow = useExecutionStore((s) => s.completeWorkflow);

  useEffect(() => {
    if (!executionId) return;

    // Build WebSocket URL relative to current host
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws/executions/${executionId}`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log(`[WS] Connected to execution ${executionId}`);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        switch (data.type) {
          case "agent_status":
            updateAgentStatus(data.agent_id, data.status);
            break;

          case "agent_output_chunk":
            appendAgentOutput(data.agent_id, data.chunk);
            break;

          case "agent_completed":
            completeAgent(
              data.agent_id,
              data.tokens_used ?? 0,
              data.latency_ms ?? 0,
            );
            break;

          case "workflow_completed":
            completeWorkflow(data.status, data.total_tokens ?? 0);
            break;

          case "error":
            console.error("[WS] Execution error:", data.message);
            if (data.agent_id) {
              updateAgentStatus(data.agent_id, "failed");
            }
            break;
        }
      } catch (err) {
        console.error("[WS] Failed to parse message:", err);
      }
    };

    ws.onerror = (err) => {
      console.error("[WS] WebSocket error:", err);
    };

    ws.onclose = () => {
      console.log(`[WS] Disconnected from execution ${executionId}`);
    };

    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [executionId, updateAgentStatus, appendAgentOutput, completeAgent, completeWorkflow]);

  /** Send a cancel message to the server. */
  const cancelExecution = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "cancel", execution_id: executionId }));
    }
  };

  return { cancelExecution };
}