// One day on the Week page: when the reminder goes out, the first class, and the suggested lot
// (switchable between Best / Cheapest / Closest). Skipped days say why (holiday, finals week, no classes).
// Click the time to change this day's reminder; on a day without one, "Add reminder" creates it.
import { useState } from "react";

import type { LotPick, Priority, ReminderDay } from "../api/types";
import { isoDate, monthDay, parseDate, weekdayShort } from "../lib/dates";
import { formatTime } from "../lib/schedule";
import { ReminderTimeEditor } from "./ReminderTimeEditor";
import { Icon, ZonePlate } from "./ui";

const CHIPS: { priority: Priority; label: string }[] = [
  { priority: "best", label: "Best" },
  { priority: "cheapest", label: "Cheapest" },
  { priority: "closest", label: "Closest" },
];

const dollars = (cents: number) => `$${(cents / 100).toFixed(2)}`;
const capitalize = (text: string) => text.charAt(0).toUpperCase() + text.slice(1);

type Props = {
  day: ReminderDay;
  defaultPriority: Priority;
  walkLimit: number;
  /** Save a time the user chose for this day ("HH:MM"), or remove it (back to automatic) */
  setTime: (date: string, remindAt: string) => Promise<void>;
  clearTime: (date: string) => Promise<void>;
};

/** A sensible starting time for a new reminder: a couple of minutes from now today, 9:00 otherwise */
function suggestedTime(date: string): string {
  const now = new Date();
  if (date !== isoDate(now)) return "09:00";
  const soon = new Date(now.getTime() + 2 * 60000);
  return `${String(soon.getHours()).padStart(2, "0")}:${String(soon.getMinutes()).padStart(2, "0")}`;
}

export function DayCard({ day, defaultPriority, walkLimit, setTime, clearTime }: Props) {
  const [priority, setPriority] = useState<Priority>(defaultPriority);
  const [editing, setEditing] = useState(false);
  const date = parseDate(day.date);
  const canEdit = day.date >= isoDate(new Date());          // no reminders for days already gone
  const editor = (initial: string, isCustom: boolean) => (
    <ReminderTimeEditor initial={initial} isCustom={isCustom}
                        onSave={(remindAt) => setTime(day.date, remindAt)}
                        onReset={() => clearTime(day.date)} onCancel={() => setEditing(false)} />
  );

  if ("skipped" in day) {
    return (
      <article className={`day-card skipped ${day.skipped === "weekend" ? "weekend" : ""}`}>
        <div className="day-card-heading"><strong>{weekdayShort(date)}</strong><span>{monthDay(date)}</span></div>
        <div className="skipped-content">
          <Icon name="calendar" size={24} />
          <strong>{capitalize(day.skipped)}</strong>
          <span>{day.skipped === "weekend" ? "Parking isn't enforced." : "No reminder today."}</span>
          {canEdit && !editing && <button className="add-reminder-button" onClick={() => setEditing(true)}>+ Add reminder</button>}
        </div>
        {editing && editor(suggestedTime(day.date), false)}
      </article>
    );
  }

  const [time, meridiem] = formatTime(day.remind_at).split(" ");
  const suggestion = day.suggestion;
  const lot: LotPick | null = suggestion ? suggestion.picks[priority] : null;

  return (
    <article className="day-card">
      <div className="day-card-heading">
        <span><strong>{weekdayShort(date)}</strong> {monthDay(date)}</span>
      </div>
      <span className="overline">Reminder{day.custom && <em className="custom-badge">Your time</em>}</span>
      {editing ? editor(day.remind_at, day.custom) : (
        <button className="time-button" onClick={() => canEdit && setEditing(true)} disabled={!canEdit}
                title={canEdit ? "Change this day's reminder time" : undefined}>
          <time className="big-time">{time} <small>{meridiem}</small></time>
          {canEdit && <span className="time-edit-hint">Edit</span>}
        </button>
      )}
      {day.first_class ? (
        <p className="first-class">
          <strong>{day.first_class.course}</strong> at {formatTime(day.first_class.start)}
          <br /><span>{day.first_class.building_name ?? "No building set"}</span>
        </p>
      ) : (
        <p className="first-class"><strong>Reminder you added</strong><br /><span>No classes this day</span></p>
      )}

      {!day.first_class ? null : suggestion && lot ? (
        <>
          <div className="filter-chips" role="radiogroup" aria-label="Parking priority">
            {CHIPS.map((chip) => (
              <button key={chip.priority} role="radio" aria-checked={priority === chip.priority}
                      className={priority === chip.priority ? "active" : ""} onClick={() => setPriority(chip.priority)}>
                {chip.label}
              </button>
            ))}
          </div>
          <div className="lot-result" key={priority}>
            <div className="lot-title">
              <ZonePlate zone={lot.zone} large />
              <span><strong>{lot.lot_name}</strong><small>{priority === defaultPriority ? "Suggested for you" : capitalize(priority)}</small></span>
            </div>
            <div className="lot-numbers">
              <strong>{dollars(lot.price_cents)}</strong>
              {/* "~" only when the walk is our straight-line estimate rather than Google's real route */}
              <span className={lot.over_walk_limit ? "over-limit" : ""}>
                {lot.walk_source === "estimate" ? "~" : ""}{lot.walk_min} min walk
              </span>
            </div>
            {/* Savings, the walk-limit check and access notes all come from the API */}
            {lot.saves_cents > 0 && <span className="savings-pill">Saves {dollars(lot.saves_cents)} vs {suggestion.closest.lot_name}</span>}
            {lot.over_walk_limit && <small className="limit-note">Longer than your {walkLimit}-min walk limit</small>}
            {lot.access_note && <small className="limit-note muted">{lot.access_note}</small>}
            <a className="directions-link" href={lot.directions_url} target="_blank" rel="noopener">
              <Icon name="location" size={16} /> Directions
            </a>
          </div>
        </>
      ) : (
        <p className="no-tip">Add a building to this day's classes for a parking tip.</p>
      )}
    </article>
  );
}
