import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { extractErrorMessage } from "../../api/client";
import { createGoalContribution, deleteContribution, listGoalContributions } from "../../api/contributions";
import { getGoal } from "../../api/goals";
import type { Contribution, SavingsGoal } from "../../types";
import { formatDate, formatMoney, formatPct, today } from "../../utils/format";

export function GoalDetailPage() {
  const { id } = useParams<{ id: string }>();
  const goalId = Number(id);
  const navigate = useNavigate();

  const [goal, setGoal] = useState<SavingsGoal | null>(null);
  const [contributions, setContributions] = useState<Contribution[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [amount, setAmount] = useState("");
  const [date, setDate] = useState(today());
  const [note, setNote] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [goalRes, contributionsRes] = await Promise.all([
        getGoal(goalId),
        listGoalContributions(goalId),
      ]);
      setGoal(goalRes.data);
      setContributions(contributionsRes.data);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!Number.isNaN(goalId)) {
      load();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [goalId]);

  async function handleAddContribution(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await createGoalContribution(goalId, { amount, date, note: note || undefined });
      setAmount("");
      setNote("");
      setDate(today());
      await load();
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDeleteContribution(contributionId: number) {
    if (!confirm("Delete this contribution?")) return;
    setError(null);
    try {
      await deleteContribution(contributionId);
      await load();
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }

  if (Number.isNaN(goalId)) {
    return <p className="form-error">Invalid goal id.</p>;
  }

  return (
    <div>
      <div className="page-header">
        <h1>{goal ? goal.name : "Goal"}</h1>
        <button className="secondary" onClick={() => navigate("/goals")}>Back to goals</button>
      </div>

      {error && <div className="form-error">{error}</div>}

      {loading || !goal ? (
        <p>Loading...</p>
      ) : (
        <>
          <div className="card">
            <div className="summary-grid">
              <div className="summary-tile">
                <div className="label">Saved</div>
                <div className="value positive">{formatMoney(goal.saved_amount)}</div>
              </div>
              <div className="summary-tile">
                <div className="label">Target</div>
                <div className="value">{formatMoney(goal.target_amount)}</div>
              </div>
              <div className="summary-tile">
                <div className="label">Progress</div>
                <div className="value">{formatPct(goal.progress_pct)}</div>
              </div>
            </div>
            <div className="progress-bar-track">
              <div className="progress-bar-fill" style={{ width: `${Math.min(100, parseFloat(goal.progress_pct))}%` }} />
            </div>
            <p className="muted" style={{ marginTop: "0.75rem" }}>
              {goal.target_date && <>Target date: {formatDate(goal.target_date)}. </>}
              {goal.projected_completion_date
                ? <>Projected completion at current rate: {formatDate(goal.projected_completion_date)}.</>
                : <>Not enough contribution history yet to project a completion date.</>}
            </p>
          </div>

          <div className="card">
            <h2>Add a contribution</h2>
            <form className="inline-form" onSubmit={handleAddContribution}>
              <label>
                Amount
                <input type="number" step="0.01" min="0.01" value={amount} onChange={(e) => setAmount(e.target.value)} required />
              </label>
              <label>
                Date
                <input type="date" value={date} onChange={(e) => setDate(e.target.value)} required />
              </label>
              <label>
                Note (optional)
                <input value={note} onChange={(e) => setNote(e.target.value)} />
              </label>
              <button type="submit" disabled={submitting}>Add</button>
            </form>
          </div>

          <div className="card">
            <h2>Contribution history</h2>
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Amount</th>
                  <th>Note</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {contributions.map((c) => (
                  <tr key={c.id}>
                    <td>{formatDate(c.date)}</td>
                    <td>{formatMoney(c.amount)}</td>
                    <td>{c.note || <span className="muted">-</span>}</td>
                    <td className="actions">
                      <button className="danger" onClick={() => handleDeleteContribution(c.id)}>Delete</button>
                    </td>
                  </tr>
                ))}
                {contributions.length === 0 && (
                  <tr><td colSpan={4} className="muted">No contributions yet.</td></tr>
                )}
              </tbody>
            </table>
          </div>

          <p><Link to="/goals">&larr; All goals</Link></p>
        </>
      )}
    </div>
  );
}
