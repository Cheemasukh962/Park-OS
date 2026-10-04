// The Schedule page: the saved classes on the week grid. Click one to edit or delete it,
// or an empty slot to add one. Every change is saved to the API straight away.
import { useEffect, useState } from "react";

import { addClass, ApiRequestError, deleteClass, listClasses, updateClass } from "../api/client";
import type { SavedClass } from "../api/types";
import { ClassPanel } from "../components/ClassPanel";
import { Button, Heading } from "../components/ui";
import { WeekGrid } from "../components/WeekGrid";
import { type DraftClass, toDraft, toInput, toMinutes } from "../lib/schedule";

const fromSaved = (saved: SavedClass): DraftClass => toDraft({ ...saved });

export function SchedulePage({ uploadSchedule }: { uploadSchedule: () => void }) {
  const [classes, setClasses] = useState<DraftClass[]>([]);
  const [selected, setSelected] = useState<DraftClass | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listClasses().then((saved) => setClasses(saved.map(fromSaved))).catch((problem) => setError(problem.message));
  }, []);

  const run = async (action: () => Promise<void>) => {
    setError(null);
    try {
      await action();
      setSelected(null);
    } catch (problem) {
      setError(problem instanceof ApiRequestError ? problem.message : "Something went wrong.");
    }
  };

  const save = (item: DraftClass) => run(async () => {
    const saved = item.id ? await updateClass(item.id, toInput(item)) : await addClass(toInput(item));
    const next = fromSaved(saved);
    setClasses((current) => (item.id ? current.map((c) => (c.id === item.id ? next : c)) : [...current, next]));
  });
  const remove = (item: DraftClass) => run(async () => {
    if (item.id) await deleteClass(item.id);
    setClasses((current) => current.filter((c) => c.key !== item.key));
  });
  const addAt = (day: number, start: string) => {
    const end = toMinutes(start) + 50;
    setSelected(toDraft({ course: "", days: [day], start,
                          end: `${String(Math.floor(end / 60)).padStart(2, "0")}:${String(end % 60).padStart(2, "0")}` }));
  };

  const missing = classes.filter((item) => !item.building_id);
  return (
    <>
      <div className="page-header">
        <div><span className="eyebrow">Fall quarter</span><Heading>Schedule</Heading><p>{classes.length} classes</p></div>
        <div className="page-actions">
          <Button variant="secondary" icon="upload" onClick={uploadSchedule}>Upload schedule</Button>
          <Button icon="plus" onClick={() => addAt(1, "10:00")}>Add class</Button>
        </div>
      </div>
      {error && <p className="form-error" role="alert">{error}</p>}
      <div className="schedule-shell">
        <div className="schedule-grid-card">
          <div className="schedule-note"><span>Click a class to edit it</span><span><i className="legend-block" /> Your classes</span></div>
          <WeekGrid classes={classes} selectedKey={selected?.key} onSelect={setSelected} onAddAt={addAt} />
        </div>
        <aside className="schedule-aside">
          <span className="eyebrow">Quick check</span>
          <Heading level={2}>{missing.length === 0 ? "Every class has a building" : `${missing.length} ${missing.length === 1 ? "class needs" : "classes need"} a building`}</Heading>
          <p>{missing.length === 0
            ? "You'll get parking tips for every class day."
            : `Add a building to ${missing.map((item) => item.course).join(", ")} for parking tips. Reminders still go out without one.`}</p>
        </aside>
      </div>
      {selected && (
        <div className="panel-overlay" onClick={() => setSelected(null)}>
          <div onClick={(event) => event.stopPropagation()}>
            <ClassPanel item={selected} onSave={save} onDelete={remove} onClose={() => setSelected(null)} />
          </div>
        </div>
      )}
    </>
  );
}
