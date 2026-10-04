// Side panel for checking or editing one class: name, days, times, building, and whether to keep it.
import { useEffect, useState } from "react";

import { ApiRequestError, validateClass } from "../api/client";
import { type DraftClass, DAY_NAMES, toInput, WEEKDAYS } from "../lib/schedule";
import { BuildingPicker } from "./BuildingPicker";
import { Button, Field, Heading } from "./ui";

type Props = {
  item: DraftClass;
  onSave: (item: DraftClass) => void;
  onDelete: (item: DraftClass) => void;
  onClose: () => void;
};

export function ClassPanel({ item, onSave, onDelete, onClose }: Props) {
  const [draft, setDraft] = useState(item);
  const [problem, setProblem] = useState<string | null>(null);
  const [checking, setChecking] = useState(false);
  useEffect(() => { setDraft(item); setProblem(null); }, [item]);   // a different class was clicked

  const update = (changes: Partial<DraftClass>) => setDraft((current) => ({ ...current, ...changes }));
  const toggleDay = (day: number) =>
    update({ days: draft.days.includes(day) ? draft.days.filter((d) => d !== day) : [...draft.days, day].sort() });

  // The API checks the class (the rules live only there) and sends it back tidied, e.g. "9:00" → "09:00"
  const save = async () => {
    setChecking(true);
    setProblem(null);
    try {
      onSave({ ...draft, ...(await validateClass(toInput(draft))) });
    } catch (error) {
      setProblem(error instanceof ApiRequestError ? error.message : "Couldn't check this class.");
    } finally {
      setChecking(false);
    }
  };

  return (
    <aside className="details-panel">
      <div className="panel-header">
        <div><span className="eyebrow">Class details</span><Heading level={2}>{item.course || "New class"}</Heading></div>
        <button className="icon-button" onClick={onClose} aria-label="Close">×</button>
      </div>

      {draft.location && <p className="helper">From your file: {draft.location}</p>}
      <Field label="Course" value={draft.course} placeholder="ECS 36A Lecture" onChange={(course) => update({ course })} />
      <div className="field">
        <span>Days</span>
        <div className="day-toggles">
          {WEEKDAYS.map((day) => (
            <button key={day} type="button" className={draft.days.includes(day) ? "active" : ""}
                    aria-pressed={draft.days.includes(day)} onClick={() => toggleDay(day)}>
              {DAY_NAMES[day].slice(0, 2)}
            </button>
          ))}
        </div>
      </div>
      <div className="field-row">
        <Field label="Starts (24 h)" value={draft.start} placeholder="9:00" onChange={(start) => update({ start })} />
        <Field label="Ends (24 h)" value={draft.end ?? ""} placeholder="10:50" onChange={(end) => update({ end: end || null })} />
      </div>
      <BuildingPicker
        value={{ id: draft.building_id, name: draft.building_name }}
        onChange={(building) => update({ building_id: building?.id ?? null, building_name: building?.name ?? null })}
      />
      <label className="include-toggle">
        <input type="checkbox" checked={draft.include} onChange={(event) => update({ include: event.target.checked })} />
        <span>
          Remind me about this class
          {draft.online && <small>Online class: no parking needed</small>}
          {draft.registered === false && <small>Your file says you're not registered</small>}
        </span>
      </label>

      {problem && <p className="form-error">{problem}</p>}
      <div className="panel-actions">
        <Button variant="ghost" onClick={() => onDelete(item)}>Delete</Button>
        <Button onClick={save} disabled={checking}>{checking ? "Checking…" : "Save class"}</Button>
      </div>
    </aside>
  );
}
