// Inline editor for one day's reminder time: pick a time and Save, or go back to the automatic time.
// The API checks the time (not in the past, valid) and says what's wrong if it isn't.
import { useState } from "react";

import { ApiRequestError } from "../api/client";
import { Button } from "./ui";

type Props = {
  initial: string;                                   // "HH:MM"
  isCustom: boolean;                                 // show "Back to automatic"?
  onSave: (remindAt: string) => Promise<void>;
  onReset: () => Promise<void>;
  onCancel: () => void;
};

export function ReminderTimeEditor({ initial, isCustom, onSave, onReset, onCancel }: Props) {
  const [value, setValue] = useState(initial);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async (action: () => Promise<void>) => {
    setBusy(true);
    setError(null);
    try {
      await action();
    } catch (problem) {
      setError(problem instanceof ApiRequestError ? problem.message : "Couldn't save that reminder.");
      setBusy(false);
    }
  };

  return (
    <div className="reminder-editor">
      <label className="field">
        <span>Remind me at</span>
        <input type="time" value={value} onChange={(event) => setValue(event.target.value)} autoFocus />
      </label>
      {error && <p className="form-error" role="alert">{error}</p>}
      <div className="reminder-editor-actions">
        <Button onClick={() => run(() => onSave(value))} disabled={busy || !value}>{busy ? "Saving…" : "Save"}</Button>
        <Button variant="ghost" onClick={onCancel} disabled={busy}>Cancel</Button>
      </div>
      {isCustom && (
        <button className="skip-link" onClick={() => run(onReset)} disabled={busy}>Back to automatic</button>
      )}
    </div>
  );
}
