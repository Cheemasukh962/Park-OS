// Settings: kept simple on purpose. Reminders on/off, where they go, who you are, and your schedule.
// (Lead time and walk limit were taken out to keep things simple; the back end still has defaults
// for them: 30 min before class and a 10-min walk.)
import { useEffect, useState } from "react";

import { listClasses } from "../api/client";
import type { Settings } from "../api/types";
import { Button, Heading, Icon } from "../components/ui";

type Props = {
  settings: Settings;
  saveSettings: (changes: Partial<Settings>) => Promise<void>;
  editEmail: () => void;
  uploadSchedule: () => void;
};

export function SettingsPage({ settings, saveSettings, editEmail, uploadSchedule }: Props) {
  const [classCount, setClassCount] = useState<number | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    listClasses().then((classes) => setClassCount(classes.length)).catch(() => setClassCount(null));
  }, []);

  const toggleReminders = async () => {
    await saveSettings({ reminders_enabled: !settings.reminders_enabled });
    setSaved(true);
    window.setTimeout(() => setSaved(false), 1800);
  };

  return (
    <>
      <div className="page-header"><div><span className="eyebrow">Make ParkOS yours</span><Heading>Settings</Heading><p>Changes save as you make them.</p></div></div>
      <div className="settings-layout">
        <section className="settings-card">
          <div className="settings-heading"><span className="settings-icon"><Icon name="mail" /></span><div><Heading level={2}>Reminders</Heading><p>One email before your first class.</p></div></div>
          <div className="settings-row">
            <span><strong>Daily reminders</strong><small>Class days, plus any you add</small></span>
            <button className={`toggle ${settings.reminders_enabled ? "on" : ""}`} role="switch"
                    aria-checked={settings.reminders_enabled} onClick={toggleReminders}><span /></button>
          </div>
          <button className="settings-row settings-link" onClick={editEmail}>
            <span><strong>Email</strong><small>Where your reminders go</small></span>
            <span className="setting-value">{settings.email || "Not set"} <Icon name="chevron" /></span>
          </button>
        </section>
        <section className="settings-card">
          <div className="settings-heading"><span className="settings-icon"><Icon name="user" /></span><div><Heading level={2}>About you</Heading><p>Used to find the lots you're allowed to use.</p></div></div>
          <div className="settings-row"><span><strong>Affiliation</strong><small>Parking access and prices</small></span><span className="setting-value">Student</span></div>
        </section>
        <section className="settings-card">
          <div className="settings-heading"><span className="settings-icon"><Icon name="calendar" /></span>
            <div><Heading level={2}>Schedule</Heading>
              <p>{classCount == null ? "Loading…" : `${classCount} ${classCount === 1 ? "class" : "classes"} saved.`}</p></div></div>
          <div className="settings-buttons"><Button variant="secondary" icon="upload" onClick={uploadSchedule}>Upload a new schedule</Button></div>
        </section>
      </div>
      {saved && <div className="toast"><Icon name="check" /> Saved</div>}
    </>
  );
}
