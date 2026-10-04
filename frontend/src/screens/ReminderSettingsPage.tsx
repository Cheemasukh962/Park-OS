// "Edit reminders": on/off, email, and how long before the first class the reminder goes out.
// The preview card shows the next real reminder with the chosen timing.
import { useEffect, useState } from "react";

import { ApiRequestError, reminderPreview } from "../api/client";
import type { ReminderDay, Settings } from "../api/types";
import { Button, Field, Heading, Icon, ZonePlate } from "../components/ui";
import { addDays, isoDate, parseDate } from "../lib/dates";
import { formatTime } from "../lib/schedule";

const LEAD_OPTIONS = [60, 45, 30, 15];          // minutes before the first class

type Props = {
  settings: Settings;
  saveSettings: (changes: Partial<Settings>) => Promise<void>;
  onDone: () => void;
};

export function ReminderSettingsPage({ settings, saveSettings, onDone }: Props) {
  const [enabled, setEnabled] = useState(settings.reminders_enabled);
  const [email, setEmail] = useState(settings.email);
  const [lead, setLead] = useState(settings.lead_minutes);
  const [next, setNext] = useState<Extract<ReminderDay, { remind_at: string }> | null>(null);
  const [error, setError] = useState<string | null>(null);

  // The next real class day in the coming two weeks, previewed with the lead time picked here
  // (the API works out the reminder time, so this page never does that maths itself)
  useEffect(() => {
    const today = new Date();
    reminderPreview(isoDate(today), isoDate(addDays(today, 14)), lead)
      .then((preview) => setNext((preview.days.find((day) => "remind_at" in day) as typeof next) ?? null))
      .catch(() => setNext(null));
  }, [lead]);

  const save = async () => {
    setError(null);
    try {
      await saveSettings({ reminders_enabled: enabled, email: email.trim(), lead_minutes: lead });
      onDone();
    } catch (problem) {
      setError(problem instanceof ApiRequestError ? problem.message : "Couldn't save your settings.");
    }
  };

  const previewTime = next ? formatTime(next.remind_at) : null;
  const tip = next?.suggestion;

  return (
    <>
      <div className="page-header reminder-page-header">
        <div>
          <button className="back-link" onClick={onDone}><Icon name="arrow-left" size={17} /> This week</button>
          <span className="eyebrow">Reminder preferences</span>
          <Heading>Edit reminders</Heading>
          <p>Choose when ParkOS should nudge you before your first class.</p>
        </div>
        <div className="reminder-master">
          <span><strong>Daily reminders</strong><small>{enabled ? "On for class days" : "Currently off"}</small></span>
          <button className={`toggle ${enabled ? "on" : ""}`} role="switch" aria-checked={enabled} onClick={() => setEnabled(!enabled)}><span /></button>
        </div>
      </div>
      <div className="reminder-layout reminder-settings-layout">
        <div>
          <div className="reminder-form">
            <Field label="Email address" type="email" value={email} placeholder="you@ucdavis.edu" onChange={setEmail} />
            <div className="field">
              <span>When should we remind you?</span>
              <div className="timing-options" role="radiogroup" aria-label="Reminder timing">
                {LEAD_OPTIONS.map((minutes) => (
                  <button type="button" role="radio" key={minutes} aria-checked={lead === minutes}
                          className={lead === minutes ? "active" : ""} onClick={() => setLead(minutes)}>
                    {minutes} min before
                  </button>
                ))}
              </div>
              <small className="timing-helper">Timing is based on the start of your first class that day.</small>
            </div>
            {error && <p className="form-error" role="alert">{error}</p>}
            <Button className="full-button" onClick={save}>Save reminder settings</Button>
            <small className="timing-helper">Email sending comes in a later phase; for now this sets up what will be sent.</small>
          </div>
        </div>
        <div className="preview-card">
          {next ? (
            <>
              <span className="eyebrow">{parseDate(next.date).toLocaleDateString("en-US", { weekday: "long" })}'s preview</span>
              <div className="preview-icon"><Icon name="mail" size={28} /></div>
              <span className="preview-time">{previewTime?.split(" ")[0]} <small>{previewTime?.split(" ")[1]}</small></span>
              <Heading level={2}>Time to think about parking.</Heading>
              <p>Your first class is {next.first_class.course} at {formatTime(next.first_class.start)}
                {next.first_class.building_name ? ` in ${next.first_class.building_name}` : ""}.</p>
              {tip && (
                <div className="preview-lot">
                  <ZonePlate zone={tip.zone} />
                  <span><strong>{tip.lot_name} · ${(tip.price_cents / 100).toFixed(2)}</strong>
                    <small>About {tip.walk_min} min walk</small></span>
                </div>
              )}
            </>
          ) : (
            <><span className="eyebrow">Preview</span><p>No class days in the next two weeks.</p></>
          )}
        </div>
      </div>
    </>
  );
}
