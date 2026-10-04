// One weekday on the Week page: when the reminder goes out, the first class, and the suggested lot
// (switchable between Best / Cheapest / Closest). Skipped days say why (weekend, holiday, finals week).
import { useState } from "react";

import type { LotPick, Priority, ReminderDay } from "../api/types";
import { monthDay, parseDate, weekdayShort } from "../lib/dates";
import { formatTime } from "../lib/schedule";
import { Icon, ZonePlate } from "./ui";

const CHIPS: { priority: Priority; label: string }[] = [
  { priority: "best", label: "Best" },
  { priority: "cheapest", label: "Cheapest" },
  { priority: "closest", label: "Closest" },
];

const dollars = (cents: number) => `$${(cents / 100).toFixed(2)}`;
const capitalize = (text: string) => text.charAt(0).toUpperCase() + text.slice(1);

export function DayCard({ day, defaultPriority, walkLimit }: { day: ReminderDay; defaultPriority: Priority; walkLimit: number }) {
  const [priority, setPriority] = useState<Priority>(defaultPriority);
  const date = parseDate(day.date);

  if ("skipped" in day) {
    return (
      <article className="day-card skipped">
        <div className="day-card-heading"><strong>{weekdayShort(date)}</strong><span>{monthDay(date)}</span></div>
        <div className="skipped-content">
          <Icon name="calendar" size={24} />
          <strong>{capitalize(day.skipped)}</strong>
          <span>No reminder today.</span>
        </div>
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
      <span className="overline">Reminder</span>
      <time className="big-time">{time} <small>{meridiem}</small></time>
      <p className="first-class">
        <strong>{day.first_class.course}</strong> at {formatTime(day.first_class.start)}
        <br /><span>{day.first_class.building_name ?? "No building set"}</span>
      </p>

      {suggestion && lot ? (
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
