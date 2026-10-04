// Onboarding step 4: confirm or add each class's building (optional: it's only for parking tips),
// then save the schedule. This is the first time anything is written to the server.
import { useState } from "react";

import { ApiRequestError, replaceSchedule } from "../../api/client";
import { BuildingPicker } from "../../components/BuildingPicker";
import { OnboardingShell } from "../../components/OnboardingShell";
import { Button, Heading, Icon } from "../../components/ui";
import { type DraftClass, formatDays, formatTime, toInput } from "../../lib/schedule";

type Props = {
  classes: DraftClass[];
  setClasses: (classes: DraftClass[]) => void;
  next: () => void;
  back: () => void;
};

export function BuildingsStep({ classes, setClasses, next, back }: Props) {
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const kept = classes.filter((item) => item.include);

  const setBuilding = (key: string, id: number | null, name: string | null) =>
    setClasses(classes.map((item) => (item.key === key ? { ...item, building_id: id, building_name: name } : item)));

  const finish = async () => {
    setSaving(true);
    setError(null);
    try {
      // Only the fields the API saves (toInput); the rest (room, online, ...) was just for review
      await replaceSchedule(kept.map(toInput));
      next();
    } catch (problem) {
      setError(problem instanceof ApiRequestError ? problem.message : "Couldn't save your schedule.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <OnboardingShell step={4} onBack={back}>
      <div className="step-heading">
        <span className="eyebrow">Optional, but useful</span>
        <Heading>Where are your classes?</Heading>
        <p>It's how we find you cheaper parking. You can leave any class blank: you'll still get reminders.</p>
      </div>
      <div className="building-list">
        {kept.map((item) => (
          <div className="building-row" key={item.key}>
            <div className="course-summary">
              <span className="course-initial">{item.course.slice(0, 2)}</span>
              <span>
                <strong>{item.course}</strong>
                <small>{formatDays(item.days)} · {formatTime(item.start)}{item.room ? ` · room ${item.room}` : ""}</small>
              </span>
            </div>
            <BuildingPicker label="Building" value={{ id: item.building_id, name: item.building_name }}
                            onChange={(building) => setBuilding(item.key, building?.id ?? null, building?.name ?? null)} />
            {item.building_id
              ? <span className="building-ok" title="Building set"><Icon name="check" /></span>
              : <span className="building-missing">Blank</span>}
          </div>
        ))}
      </div>
      {error && <p className="form-error upload-error" role="alert">{error}</p>}
      <div className="simple-footer">
        <span>You can change buildings later from your schedule.</span>
        <Button onClick={finish} disabled={saving}>{saving ? "Saving…" : "Save my schedule"} <Icon name="arrow-right" /></Button>
      </div>
    </OnboardingShell>
  );
}
