// "This week": one card per day from the real reminder plan (GET /api/reminders/preview).
// Click a card's time to change that day's reminder; "Add a reminder" (••• menu) creates one for any day.
import { useEffect, useState } from "react";

import { ApiRequestError, clearCustomReminder, reminderPreview, setCustomReminder } from "../api/client";
import type { ReminderPreview, Settings } from "../api/types";
import { AddReminderPanel } from "../components/AddReminderPanel";
import { DayCard } from "../components/DayCard";
import { Button, Heading, Icon } from "../components/ui";
import { addDays, isoDate, mondayOf, monthDay, parseDate } from "../lib/dates";
import { formatTime } from "../lib/schedule";

type Props = {
  settings: Settings;
  saveSettings: (changes: Partial<Settings>) => Promise<void>;
  editReminders: () => void;
};

export function WeekPage({ settings, saveSettings, editReminders }: Props) {
  const [monday, setMonday] = useState(() => mondayOf(new Date()));   // the week you're in, weekends included
  const [preview, setPreview] = useState<ReminderPreview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const [adding, setAdding] = useState(false);
  const [reloads, setReloads] = useState(0);              // bump to fetch the plan again after a change
  const setRemindersEnabled = (on: boolean) => { saveSettings({ reminders_enabled: on }).catch(() => {}); };
  const sunday = addDays(monday, 6);

  // Reload whenever the week changes, or settings that change the plan (lead time, priority, walk limit)
  useEffect(() => {
    setPreview(null);
    setError(null);
    reminderPreview(isoDate(monday), isoDate(sunday))   // Monday to Sunday
      .then(setPreview)
      .catch((problem) => setError(problem instanceof ApiRequestError ? problem.message : "Couldn't load this week."));
  }, [monday, reloads, settings.lead_minutes, settings.priority, settings.walk_limit_min, settings.affiliation]);

  // Changing a day's time: the API checks and saves it, then the week is fetched again
  const setTime = async (date: string, remindAt: string) => {
    await setCustomReminder(date, remindAt);
    setReloads((n) => n + 1);
  };
  const clearTime = async (date: string) => {
    await clearCustomReminder(date);
    setReloads((n) => n + 1);
  };
  const addReminder = async ({ email, date, remindAt }: { email: string; date: string; remindAt: string }) => {
    await setCustomReminder(date, remindAt);                // checked first: a bad time saves nothing
    if (email !== settings.email || !settings.reminders_enabled) {
      await saveSettings({ email, reminders_enabled: true });
    }
    setAdding(false);
    setMonday(mondayOf(parseDate(date)));                    // show the week the reminder is in
    setReloads((n) => n + 1);
  };

  // The next reminder and the week's savings come from the API's summary
  // All seven days: weekends show too, so you can add a reminder on them
  const days = preview?.days ?? null;
  const next = preview?.summary.next_reminder ?? null;
  const weeklySavings = preview?.summary.saves_cents_total ?? 0;

  return (
    <>
      <div className="page-header">
        <div>
          <span className="eyebrow">Your parking plan</span>
          <Heading>This week</Heading>
          <p>{monthDay(monday)} – {monthDay(sunday)}, {sunday.getFullYear()}</p>
        </div>
        <div className="page-actions">
          <div className="week-arrows">
            <button aria-label="Previous week" onClick={() => setMonday(addDays(monday, -7))}><Icon name="arrow-left" /></button>
            <button aria-label="Next week" onClick={() => setMonday(addDays(monday, 7))}><Icon name="arrow-right" /></button>
          </div>
          <div className="overflow-wrap">
            <button className="overflow-button" aria-label="This week options" aria-expanded={menuOpen} onClick={() => setMenuOpen(!menuOpen)}><Icon name="more" /></button>
            {menuOpen && (
              <div className="week-menu">
                <div className="menu-toggle-row">
                  <span><strong>Reminders</strong><small>{settings.reminders_enabled ? "On for class days" : "Currently off"}</small></span>
                  <button className={`toggle ${settings.reminders_enabled ? "on" : ""}`} role="switch" aria-checked={settings.reminders_enabled}
                          onClick={() => setRemindersEnabled(!settings.reminders_enabled)}><span /></button>
                </div>
                <button className="menu-action" onClick={() => { setMenuOpen(false); setAdding(true); }}><Icon name="plus" size={18} /><span><strong>Add a reminder</strong><small>Any day and time, weekends too</small></span><Icon name="chevron" size={16} /></button>
                <button className="menu-action" onClick={editReminders}><Icon name="clock" size={18} /><span><strong>Edit reminders</strong><small>Email and automatic timing</small></span><Icon name="chevron" size={16} /></button>
              </div>
            )}
          </div>
        </div>
      </div>

      {!settings.reminders_enabled && (
        <div className="reminders-banner">
          <span><strong>Reminders are off.</strong> Turn them on when you want a nudge before class.</span>
          <Button variant="secondary" onClick={() => setRemindersEnabled(true)}>Turn on</Button>
        </div>
      )}
      <div className="summary-strip">
        <div>
          <span className="summary-icon"><Icon name="clock" /></span>
          <span><small>Next reminder</small>
            <strong>{next
              ? `${parseDate(next.date).toLocaleDateString("en-US", { weekday: "long" })} at ${formatTime(next.remind_at)}`
              : "None this week"}</strong></span>
        </div>
        <div>
          <span className="summary-icon gold"><span>$</span></span>
          <span><small>Saved vs the closest lots</small><strong>${(weeklySavings / 100).toFixed(2)}</strong></span>
        </div>
        <p>Parking isn't enforced Saturday or Sunday.</p>
      </div>

      {error && <p className="form-error" role="alert">{error}</p>}
      {!days && !error && <p className="loading-note">Planning your week…</p>}
      {days && (
        <div className="day-card-grid">
          {days.map((day) => (
            <DayCard key={`${day.date}-${reloads}`} day={day} defaultPriority={settings.priority}
                     walkLimit={settings.walk_limit_min} setTime={setTime} clearTime={clearTime} />
          ))}
        </div>
      )}
      {adding && (
        <AddReminderPanel email={settings.email} remindersOn={settings.reminders_enabled}
                          onAdd={addReminder} onClose={() => setAdding(false)} />
      )}
    </>
  );
}
