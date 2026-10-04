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

/** The Monday of the week a date is in (weeks run Monday to Sunday). */
export function mondayOf(date: Date): Date {
  const weekday = date.getDay() === 0 ? 7 : date.getDay();   // JS: 0 = Sunday; we want Sunday = 7
  return addDays(date, 1 - weekday);
}

/** Date → "Mon" / "Oct 5" */
export const weekdayShort = (date: Date) => date.toLocaleDateString("en-US", { weekday: "short" });
export const monthDay = (date: Date) => date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
