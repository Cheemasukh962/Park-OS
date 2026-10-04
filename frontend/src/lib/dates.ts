// Calendar-date helpers. Dates are handled in the browser's local time (campus time for UC Davis
// students); never toISOString(), which converts to UTC and can shift the day.

/** Date → "2026-10-05" */
export function isoDate(date: Date): string {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

/** "2026-10-05" → a Date at local midnight */
export function parseDate(iso: string): Date {
  const [year, month, day] = iso.split("-").map(Number);
  return new Date(year, month - 1, day);
}

export function addDays(date: Date, days: number): Date {
  const copy = new Date(date);
  copy.setDate(copy.getDate() + days);
  return copy;
}

/** The Monday of the week to show: this week, or next week if it's already the weekend. */
export function currentPlanningMonday(today = new Date()): Date {
  const weekday = today.getDay();                       // 0 = Sunday ... 6 = Saturday
  if (weekday === 0) return addDays(today, 1);
  if (weekday === 6) return addDays(today, 2);
  return addDays(today, 1 - weekday);
}

/** Date → "Mon" / "Oct 5" */
export const weekdayShort = (date: Date) => date.toLocaleDateString("en-US", { weekday: "short" });
export const monthDay = (date: Date) => date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
