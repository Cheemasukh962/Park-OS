// "Add a reminder" (from the Week page's ••• menu): email, day and time → one reminder.
// Works for any day, including weekends, so reminders can be tried out live.
import { useState } from "react";

import { ApiRequestError } from "../api/client";
import { isoDate } from "../lib/dates";
import { Button, Field, Heading } from "./ui";

type Props = {
  email: string;
  remindersOn: boolean;
  /** Save the email (and turn reminders on) if needed, then add the reminder */
  onAdd: (reminder: { email: string; date: string; remindAt: string }) => Promise<void>;
  onClose: () => void;
};

function inTwoMinutes(): string {
  const soon = new Date(Date.now() + 2 * 60000);
  return `${String(soon.getHours()).padStart(2, "0")}:${String(soon.getMinutes()).padStart(2, "0")}`;
}

export function AddReminderPanel({ email: savedEmail, remindersOn, onAdd, onClose }: Props) {
  const [email, setEmail] = useState(savedEmail);
  const [date, setDate] = useState(() => isoDate(new Date()));
  const [time, setTime] = useState(inTwoMinutes);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const add = async () => {
    setBusy(true);
    setError(null);
    try {
      await onAdd({ email: email.trim(), date, remindAt: time });
    } catch (problem) {
      setError(problem instanceof ApiRequestError ? problem.message : "Couldn't add that reminder.");
      setBusy(false);
    }
  };

  return (
    <div className="panel-overlay" onClick={onClose}>
      <aside className="details-panel add-reminder-panel" onClick={(event) => event.stopPropagation()}>
        <div className="panel-header">
          <div><span className="eyebrow">One-off reminder</span><Heading level={2}>Add a reminder</Heading></div>
          <button className="icon-button" onClick={onClose} aria-label="Close">×</button>
        </div>
        <Field label="Email address" type="email" value={email} placeholder="you@ucdavis.edu" onChange={setEmail} />
        <div className="field-row">
          <label className="field">
            <span>Day</span>
            <input type="date" value={date} min={isoDate(new Date())} onChange={(event) => setDate(event.target.value)} />
          </label>
          <label className="field">
            <span>Time</span>
            <input type="time" value={time} onChange={(event) => setTime(event.target.value)} />
          </label>
        </div>
        <p className="helper">
          On a class day this replaces that day's automatic time. Any other day (weekends too) gets a reminder of its own.
          {!remindersOn && " Adding one turns reminders on."}
        </p>
        {error && <p className="form-error" role="alert">{error}</p>}
        <div className="panel-actions">
          <Button variant="ghost" onClick={onClose} disabled={busy}>Cancel</Button>
          <Button onClick={add} disabled={busy || !email.trim() || !date || !time}>{busy ? "Adding…" : "Add reminder"}</Button>
        </div>
      </aside>
    </div>
  );
}
