import { useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import { archiveGoal, createGoal, deleteGoal, listGoals, unarchiveGoal, updateGoal } from "../../api/goals";
import { extractErrorMessage } from "../../api/client";
import type { SavingsGoal } from "../../types";
import { formatDate, formatMoney, formatPct } from "../../utils/format";

export function GoalsPage() {
  const [goals, setGoals] = useState<SavingsGoal[]>([]);
  const [showArchived, setShowArchived] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [editing, setEditing] = useState<SavingsGoal | null>(null);
  const [name, setName] = useState("");
  const [targetAmount, setTargetAmount] = useState("");
  const [targetDate, setTargetDate] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function loadGoals() {
    setLoading(true);
    setError(null);
    try {
      const res = await listGoals(showArchived);
      setGoals(res.data.results);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadGoals();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [showArchived]);

  function startEdit(goal: SavingsGoal) {
    setEditing(goal);
    setName(goal.name);
    setTargetAmount(goal.target_amount);
    setTargetDate(goal.target_date ?? "");
  }

  function resetForm() {
    setEditing(null);
    setName("");
    setTargetAmount("");
    setTargetDate("");
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const payload = { name, target_amount: targetAmount, target_date: targetDate || null };
      if (editing) {
        await updateGoal(editing.id, payload);
      } else {
        await createGoal(payload);
      }
      resetForm();
      await loadGoals();
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleArchive(goal: SavingsGoal) {
    setError(null);
    try {
      if (goal.is_archived) {
        await unarchiveGoal(goal.id);
      } else {
        await archiveGoal(goal.id);
      }
      await loadGoals();
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }

  async function handleDelete(id: number) {
    if (!confirm("Delete this goal and all of its contributions?")) return;
    setError(null);
    try {
      await deleteGoal(id);
      await loadGoals();
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>Goals</h1>
        <label className="checkbox-label">
          <input type="checkbox" checked={showArchived} onChange={(e) => setShowArchived(e.target.checked)} />
          Show archived
        </label>
      </div>

      <div className="card">
        <form className="inline-form" onSubmit={handleSubmit}>
          <label>
            Name
            <input value={name} onChange={(e) => setName(e.target.value)} required />
          </label>
          <label>
            Target amount
            <input type="number" step="0.01" min="0" value={targetAmount} onChange={(e) => setTargetAmount(e.target.value)} required />
          </label>
          <label>
            Target date (optional)
            <input type="date" value={targetDate} onChange={(e) => setTargetDate(e.target.value)} />
          </label>
          <button type="submit" disabled={submitting}>{editing ? "Save" : "Add goal"}</button>
          {editing && <button type="button" className="secondary" onClick={resetForm}>Cancel</button>}
        </form>
        {error && <div className="form-error">{error}</div>}
      </div>

      <div className="card">
        {loading ? (
          <p>Loading...</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Progress</th>
                <th>Saved / Target</th>
                <th>Projected completion</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {goals.map((g) => (
                <tr key={g.id}>
                  <td><Link to={`/goals/${g.id}`}>{g.name}</Link>{g.is_archived && <span className="muted"> (archived)</span>}</td>
                  <td>{formatPct(g.progress_pct)}</td>
                  <td>{formatMoney(g.saved_amount)} / {formatMoney(g.target_amount)}</td>
                  <td>{formatDate(g.projected_completion_date)}</td>
                  <td className="actions">
                    <button className="secondary" onClick={() => startEdit(g)}>Edit</button>
                    <button className="secondary" onClick={() => handleArchive(g)}>{g.is_archived ? "Unarchive" : "Archive"}</button>
                    <button className="danger" onClick={() => handleDelete(g.id)}>Delete</button>
                  </td>
                </tr>
              ))}
              {goals.length === 0 && (
                <tr><td colSpan={5} className="muted">No goals yet.</td></tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
