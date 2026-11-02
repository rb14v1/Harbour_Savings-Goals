import { apiClient } from "./client";
import type { Contribution } from "../types";

export interface ContributionInput {
  amount: string;
  date: string;
  note?: string;
}

export function listGoalContributions(goalId: number) {
  return apiClient.get<Contribution[]>(`/goals/${goalId}/contributions/`);
}

export function createGoalContribution(goalId: number, data: ContributionInput) {
  return apiClient.post<Contribution>(`/goals/${goalId}/contributions/`, data);
}

export function deleteContribution(id: number) {
  return apiClient.delete(`/contributions/${id}/`);
}
