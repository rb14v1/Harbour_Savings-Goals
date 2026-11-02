export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  date_joined: string;
}

export interface SavingsGoal {
  id: number;
  name: string;
  target_amount: string;
  target_date: string | null;
  created_at: string;
  is_archived: boolean;
  saved_amount: string;
  progress_pct: string;
  projected_completion_date: string | null;
}

export interface Contribution {
  id: number;
  goal: number;
  amount: string;
  date: string;
  note: string;
  created_at: string;
}

export interface DashboardGoalRow {
  id: number;
  name: string;
  saved_amount: string;
  target_amount: string;
  progress_pct: string;
  projected_completion_date: string | null;
}

export interface DashboardSummary {
  total_saved: string;
  total_target: string;
  progress_pct: string;
  goals: DashboardGoalRow[];
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
