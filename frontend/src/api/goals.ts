import { apiClient } from "./client";
import type { Paginated, SavingsGoal } from "../types";

export interface GoalInput {
  name: string;
  target_amount: string;
  target_date?: string | null;
}

export function listGoals(archived?: boolean) {
  return apiClient.get<Paginated<SavingsGoal>>("/goals/", {
    params: archived === undefined ? {} : { archived },
  });
}

export function getGoal(id: number) {
  return apiClient.get<SavingsGoal>(`/goals/${id}/`);
}

export function createGoal(data: GoalInput) {
  return apiClient.post<SavingsGoal>("/goals/", data);
}

export function updateGoal(id: number, data: GoalInput) {
  return apiClient.put<SavingsGoal>(`/goals/${id}/`, data);
}

export function deleteGoal(id: number) {
  return apiClient.delete(`/goals/${id}/`);
}

export function archiveGoal(id: number) {
  return apiClient.post<SavingsGoal>(`/goals/${id}/archive/`);
}

export function unarchiveGoal(id: number) {
  return apiClient.post<SavingsGoal>(`/goals/${id}/unarchive/`);
}
