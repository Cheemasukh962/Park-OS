// Turning the API's schedule format into what the screens show, and placing classes on the week grid.
import type { ClassInput, ImportedClass } from "../api/types";

/** Weekday names by ISO number (1 = Monday). */
export const DAY_NAMES: Record<number, string> = { 1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat", 7: "Sun" };
export const WEEKDAYS = [1, 2, 3, 4, 5];

/** A class being reviewed before saving: an imported class, or one typed in by hand. */
export type DraftClass = Omit<ImportedClass, "building_match"> & {
  key: string;                       // stable id for React lists (drafts have no database id yet)
  id?: number;                       // set once the class is saved
  building_match?: string;
};

/** The fields POST/PUT /api/schedule saves; the rest of a draft is only for review. */
export function toInput({ course, days, start, end, building_id }: DraftClass): ClassInput {
  return { course, days, start, end, building_id };
}

let nextKey = 1;
export function toDraft(input: Partial<DraftClass> & Pick<DraftClass, "course" | "days" | "start">): DraftClass {
  return {
    end: null, building_id: null, building_name: null, room: null, location: null,
    online: false, registered: null, include: true, ...input, key: `draft-${nextKey++}`,
  };
}

/** "16:40" → minutes since midnight (1000). */
export function toMinutes(hhmm: string): number {
  const [hours, minutes] = hhmm.split(":").map(Number);
  return hours * 60 + minutes;
}

/** "16:40" → "4:40 pm" */
export function formatTime(hhmm: string | null): string {
  if (!hhmm) return "";
  const [hours, minutes] = hhmm.split(":").map(Number);
  const suffix = hours >= 12 ? "pm" : "am";
  return `${hours % 12 || 12}:${String(minutes).padStart(2, "0")} ${suffix}`;
}

/** [2, 4] → "Tue, Thu" */
export function formatDays(days: number[]): string {
  return days.map((day) => DAY_NAMES[day]).join(", ");
}

/** The hours the grid should show: 8 am to 5 pm, stretched to fit any earlier or later class. */
export function gridHours(classes: DraftClass[]): { first: number; last: number } {
  let first = 8;
  let last = 17;
  for (const item of classes) {
    first = Math.min(first, Math.floor(toMinutes(item.start) / 60));
    last = Math.max(last, Math.ceil(toMinutes(item.end ?? item.start) / 60));
  }
  return { first, last };
}

/** Where a class block sits in a day column, as CSS percentages of the column's height. */
export function gridPosition(item: DraftClass, first: number, last: number): { top: string; height: string } {
  const span = (last - first) * 60;
  const start = toMinutes(item.start) - first * 60;
  const end = (item.end ? toMinutes(item.end) : toMinutes(item.start) + 50) - first * 60;   // no end time: assume 50 min
  return { top: `${(start / span) * 100}%`, height: `${((end - start) / span) * 100}%` };
}

/** Why a class needs a second look, or null if it looks fine. */
export function reviewNote(item: DraftClass): string | null {
  if (item.online) return "Online: no parking";
  if (item.registered === false) return "Not registered";
  if (!item.building_id) return "Add building";
  return null;
}
