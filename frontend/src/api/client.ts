// Every call to the Flask API lives here, so screens never build URLs or parse responses themselves.
//
// How a call works: fetch() sends an HTTP request → Flask answers with JSON text →
// response.json() turns that text back into JavaScript objects → the screen puts them in state.
import type {
  Building, ClassInput, ImportResult, LotsGeoJson, Recommendations, ReminderPreview, SavedClass, Settings, TripQuery, TripRoute,
} from "./types";

/** Thrown when the API answers with an error, carrying its message for the UI to show. */
export class ApiRequestError extends Error {}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, options);
  } catch {
    throw new ApiRequestError("Can't reach the ParkOS server. Is it running?");
  }
  if (response.status === 204) return undefined as T;          // 204 No Content: nothing to parse
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    // 4xx: the API explains what was wrong. 5xx: the server itself crashed, so the details are in its terminal
    const fallback = response.status >= 500
      ? `The server hit an error (${response.status}). Check the Flask terminal for the details.`
      : `Request failed (${response.status})`;
    throw new ApiRequestError(body?.error ?? fallback);
  }
  return body as T;
}

function sendJson<T>(path: string, method: string, data: unknown): Promise<T> {
  return request<T>(path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),                                 // JavaScript object → JSON text
  });
}

// --- Schedule import ---

/** Upload an .ics or .pdf. Saves nothing: returns classes for the user to review. */
export function importSchedule(file: File): Promise<ImportResult> {
  const form = new FormData();                                  // a multipart upload, like an HTML form
  form.append("file", file);
  return request<ImportResult>("/api/schedule/import", { method: "POST", body: form });
}

// --- Schedule ---

export function listClasses(): Promise<SavedClass[]> {
  return request<SavedClass[]>("/api/schedule");
}

/** Ask the API whether a class is valid (without saving). Returns it tidied, e.g. "9:00" → "09:00";
 *  throws ApiRequestError with the reason if not. The rules live only in the back end. */
export function validateClass(input: ClassInput): Promise<ClassInput> {
  return sendJson<ClassInput>("/api/schedule/validate", "POST", input);
}

export function addClass(input: ClassInput): Promise<SavedClass> {
  return sendJson<SavedClass>("/api/schedule", "POST", input);
}

export function updateClass(id: number, input: ClassInput): Promise<SavedClass> {
  return sendJson<SavedClass>(`/api/schedule/${id}`, "PUT", input);
}

export function deleteClass(id: number): Promise<void> {
  return request<void>(`/api/schedule/${id}`, { method: "DELETE" });
}

/** Replace the whole saved schedule with these classes in ONE request (used when finishing onboarding).
 *  Either every class is saved or none is, so a save can't be left half done. */
export function replaceSchedule(classes: ClassInput[]): Promise<SavedClass[]> {
  return sendJson<SavedClass[]>("/api/schedule", "PUT", classes);
}

// --- Buildings ---

export function searchBuildings(query: string): Promise<Building[]> {
  return request<Building[]>(`/api/buildings?q=${encodeURIComponent(query)}`);
}

// --- Settings ---

export function getSettings(): Promise<Settings> {
  return request<Settings>("/api/settings");
}

/** Change only the settings given, e.g. updateSettings({ lead_minutes: 45 }). */
export function updateSettings(changes: Partial<Settings>): Promise<Settings> {
  return sendJson<Settings>("/api/settings", "PUT", changes);
}

// --- Reminders ---

/** What reminder goes out each day from `from` to `to` (dates as "YYYY-MM-DD"), and why not on skipped days.
 *  leadMinutes previews a different reminder time without saving it. */
export function reminderPreview(from: string, to: string, leadMinutes?: number): Promise<ReminderPreview> {
  const lead = leadMinutes != null ? `&lead_minutes=${leadMinutes}` : "";
  return request<ReminderPreview>(`/api/reminders/preview?from=${from}&to=${to}${lead}`);
}

/** Set this day's reminder time yourself ("HH:MM"). On a class day it replaces the automatic time;
 *  on any other day (weekend, holiday) it creates a reminder. */
export function setCustomReminder(date: string, remindAt: string): Promise<{ date: string; remind_at: string }> {
  return sendJson(`/api/reminders/custom/${date}`, "PUT", { remind_at: remindAt });
}

/** Remove a custom time: the day goes back to its automatic reminder (or none). */
export function clearCustomReminder(date: string): Promise<void> {
  return request<void>(`/api/reminders/custom/${date}`, { method: "DELETE" });
}

// --- Map: lots, recommendations and routes ---

export function getLots(): Promise<LotsGeoJson> {
  return request<LotsGeoJson>("/api/lots");
}

/** Turn a trip into URL parameters: ?building_id=439&lat=38.54&lng=-121.75&hour=10 */
function tripParams({ buildingId, location, hour }: TripQuery): URLSearchParams {
  const params = new URLSearchParams();
  if (buildingId != null) params.set("building_id", String(buildingId));
  if (location) {
    params.set("lat", location.lat.toFixed(5));
    params.set("lng", location.lng.toFixed(5));
  }
  if (hour != null) params.set("hour", String(hour));
  return params;
}

/** Best / Cheapest / Closest and the top 10 lots for a trip. */
export function getRecommendations(trip: TripQuery): Promise<Recommendations> {
  return request<Recommendations>(`/api/recommendations?${tripParams(trip)}`);
}

/** The drive and/or walk shapes to one lot, for drawing on the map. */
export function getRoute(lotId: number, trip: TripQuery): Promise<TripRoute> {
  const params = tripParams(trip);
  params.set("lot_id", String(lotId));
  params.delete("hour");
  return request<TripRoute>(`/api/route?${params}`);
}
