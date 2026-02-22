/**
 * Workflow API client.
 *
 * Provides typed functions for workflow CRUD operations.
 * All functions return the response data directly (unwrapped from axios).
 */

import { api } from "./api";
import type { Workflow, WorkflowCreatePayload, WorkflowUpdatePayload } from "../types/workflow";

interface WorkflowListResponse {
  workflows: Workflow[];
  total: number;
}

export async function createWorkflow(
  data: WorkflowCreatePayload,
): Promise<Workflow> {
  const res = await api.post<Workflow>("/workflows", data);
  return res.data;
}

export async function listWorkflows(): Promise<WorkflowListResponse> {
  const res = await api.get<WorkflowListResponse>("/workflows");
  return res.data;
}

export async function getWorkflow(id: string): Promise<Workflow> {
  const res = await api.get<Workflow>(`/workflows/${id}`);
  return res.data;
}

export async function updateWorkflow(
  id: string,
  data: WorkflowUpdatePayload,
): Promise<Workflow> {
  const res = await api.put<Workflow>(`/workflows/${id}`, data);
  return res.data;
}

export async function deleteWorkflow(id: string): Promise<void> {
  await api.delete(`/workflows/${id}`);
}