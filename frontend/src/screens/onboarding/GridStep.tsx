// Onboarding step 3: check the classes on a week grid. Click a class to edit it,
// or an empty slot to add one. Nothing is saved until the end of onboarding.
import { useState } from "react";

import type { ImportResult } from "../../api/types";
import { ClassPanel } from "../../components/ClassPanel";
import { OnboardingShell } from "../../components/OnboardingShell";
import { Button, Heading, Icon } from "../../components/ui";
import { WeekGrid } from "../../components/WeekGrid";
import { type DraftClass, toDraft, toMinutes } from "../../lib/schedule";

type Props = {
  classes: DraftClass[];
  setClasses: (classes: DraftClass[]) => void;
  imported: ImportResult | null;
  next: () => void;
  back: () => void;
};

export function GridStep({ classes, setClasses, imported, next, back }: Props) {
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const selected = classes.find((item) => item.key === selectedKey) ?? null;
  const included = classes.filter((item) => item.include);

  const addAt = (day: number, start: string) => {
    const endMinutes = toMinutes(start) + 50;
    const end = `${String(Math.floor(endMinutes / 60)).padStart(2, "0")}:${String(endMinutes % 60).padStart(2, "0")}`;
    const item = toDraft({ course: "", days: [day], start, end });
    setClasses([...classes, item]);
    setSelectedKey(item.key);
  };
  const save = (item: DraftClass) => {
    setClasses(classes.map((current) => (current.key === item.key ? item : current)));
    setSelectedKey(null);
  };
  const remove = (item: DraftClass) => {
    setClasses(classes.filter((current) => current.key !== item.key));
    setSelectedKey(null);
  };

  return (
    <OnboardingShell step={3} onBack={back}>
      <div className="grid-step-heading">
        <div>
          <span className="eyebrow">Your weekly rhythm</span>
          <Heading>{imported ? "Check your classes" : "Mark your class times"}</Heading>
          <p>Click any class to fine-tune its details, or click an empty time to add one.</p>
        </div>
      </div>
      {imported && (
        <div className="import-summary">
          <Icon name="check" />
          <span>
            Found <strong>{imported.classes.length}</strong> classes in your {imported.source === "ics" ? "calendar file" : "PDF"}.
            {" "}{imported.classes.length - imported.classes.filter((c) => c.include).length > 0 &&
              "Faded ones are unticked (online or not registered): click to change."}
            {imported.skipped.length > 0 && ` Skipped ${imported.skipped.length} one-time events, like final exams.`}
          </span>
        </div>
      )}
      <div className="grid-workspace">
        <WeekGrid classes={classes} selectedKey={selectedKey}
                  onSelect={(item) => setSelectedKey(item.key)} onAddAt={addAt} />
        {selected && <ClassPanel item={selected} onSave={save} onDelete={remove} onClose={() => setSelectedKey(null)} />}
      </div>
      <div className="sticky-footer">
        <span><strong>{included.length}</strong> {included.length === 1 ? "class" : "classes"} with reminders</span>
        <Button onClick={next} disabled={included.length === 0}>Continue <Icon name="arrow-right" /></Button>
      </div>
    </OnboardingShell>
  );
}
