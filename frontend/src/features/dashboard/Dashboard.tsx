import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { fetchDashboard } from "../../api/dashboard";
import { extractErrorMessage } from "../../api/client";
import type { DashboardSummary } from "../../types";
import { formatDate, formatMoney, formatPct } from "../../utils/format";

export function Dashboard() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetchDashboard()
      .then((res) => setSummary(res.data))
      .catch((err) => setError(extractErrorMessage(err)))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <div className="page-header">
        <h1>Dashboard</h1>
      </div>

      {error && <div className="form-error">{error}</div>}

      {loading || !summary ? (
        <p>Loading...</p>
      ) : (
        <>
          <div className="summary-grid">
            <div className="summary-tile">
              <div className="label">Total saved</div>
              <div className="value positive">{formatMoney(summary.total_saved)}</div>
            </div>
            <div className="summary-tile">
              <div className="label">Total target</div>
              <div className="value">{formatMoney(summary.total_target)}</div>
            </div>
            <div className="summary-tile">
              <div className="label">Overall progress</div>
              <div className="value">{formatPct(summary.progress_pct)}</div>
            </div>
          </div>

          <div className="card">
            <h2>Active goals</h2>
            {summary.goals.length === 0 && <p className="muted">No active goals yet. <Link to="/goals">Add one.</Link></p>}
            {summary.goals.map((goal) => {
              const pct = parseFloat(goal.progress_pct);
              return (
                <div className="goal-row" key={goal.id}>
                  <div className="goal-row-header">
                    <Link to={`/goals/${goal.id}`}>{goal.name}</Link>
                    <span>
                      {formatMoney(goal.saved_amount)} / {formatMoney(goal.target_amount)}
                    </span>
                  </div>
                  <div className="progress-bar-track">
                    <div className="progress-bar-fill" style={{ width: `${Math.min(100, pct)}%` }} />
                  </div>
                  <div className="goal-row-footer muted">
                    {formatPct(goal.progress_pct)} saved
                    {goal.projected_completion_date && (
                      <> · projected completion {formatDate(goal.projected_completion_date)}</>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
