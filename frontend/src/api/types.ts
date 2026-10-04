// The JSON shapes the Flask API sends and receives (docs/PRD.md section 6).
// Keeping them typed means TypeScript warns us if the front end and back end drift apart.

/** Days are ISO numbers: 1 = Monday ... 7 = Sunday. Times are 24-hour "HH:MM". */
export type Day = 1 | 2 | 3 | 4 | 5 | 6 | 7;

/** A class as saved by POST /api/schedule. */
export type ClassInput = {
  course: string;
  days: number[];
  start: string;
  end: string | null;
  building_id: number | null;
};

/** A saved class, as returned by GET /api/schedule. */
export type SavedClass = ClassInput & {
  id: number;
  building_name: string | null;
};

/** One class found in an uploaded file (POST /api/schedule/import). Extra fields help the user review it. */
export type ImportedClass = ClassInput & {
  building_name: string | null;
  room: string | null;
  location: string | null;
  building_match: string;
  online: boolean;
  registered: boolean | null;
  include: boolean;
};

export type ImportResult = {
  source: "ics" | "pdf";
  classes: ImportedClass[];
  skipped: { text: string; reason: string }[];
};

export type Building = {
  id: number;
  caan: string | null;
  name: string;
  category: string;
};

/** Every error from the API looks like this, with status 400 or 404. */
export type ApiError = { error: string };

export type Affiliation = "student" | "staff" | "visitor";
export type Priority = "best" | "cheapest" | "closest";

/** GET/PUT /api/settings. PUT sends only the keys being changed. */
export type Settings = {
  affiliation: Affiliation;
  lead_minutes: number;
  walk_limit_min: number;
  priority: Priority;
  reminders_enabled: boolean;
  channel: "email";
  email: string;
};

/** One suggested lot for a day. walk_min is the day's LONGEST walk (to the furthest class building). */
export type LotPick = {
  lot_id: number;
  lot_name: string;
  zone: string;
  price_cents: number;
  walk_min: number;
  metres: number;
  walk_source: "google" | "estimate";
  directions_url: string;
  // Decided by the API so every screen agrees:
  saves_cents: number;             // vs the closest lot (negative = costs more)
  over_walk_limit: boolean;
  access_note: string | null;      // e.g. "A: students after 5 pm"
};

/** One day from GET /api/reminders/preview: either a reminder, or the reason there isn't one. */
export type ReminderDay =
  | { date: string; skipped: string }
  | {
      date: string;
      remind_at: string;                                   // "09:30"
      first_class: { course: string; start: string; building_name: string | null };
      message: string;
      suggestion: (LotPick & { closest: LotPick; picks: Record<Priority, LotPick> }) | null;
    };

/** GET /api/reminders/preview */
export type ReminderPreview = {
  days: ReminderDay[];
  summary: { next_reminder: { date: string; remind_at: string } | null; saves_cents_total: number };
};

/** One lot in a trip (GET /api/recommendations). A leg is null when it doesn't apply
 *  (no walk without a class building, no drive without the user's location). */
export type TripOption = {
  lot_id: number;
  lot_name: string;
  zone: string;
  price_cents: number;
  walk_min: number | null;
  metres: number | null;
  walk_source: "google" | "estimate" | null;
  drive_min: number | null;
  drive_metres: number | null;
  total_min: number;
  directions_url: string;
  // Decided by the API so every screen agrees:
  saves_cents: number;             // vs the closest lot (negative = costs more)
  over_walk_limit: boolean;
  access_note: string | null;      // e.g. "A: students after 5 pm"
};

export type Recommendations = {
  building: string | null;
  building_id: number | null;
  building_centre: [number, number] | null;        // [lat, lng]
  from_location: boolean;
  far_from_campus: boolean;
  affiliation: Affiliation;
  hour: number;
  /** Which hour the lots are for, and why: sent by us, the next class at this building (arriving early), or now. */
  arrival: { hour: number; reason: "given" | "next class" | "now"; course?: string; date?: string; start?: string };
  allowed_lot_ids: number[];                       // every lot this user may park in at that hour
  walk_limit_min: number;
  best: TripOption | null;
  cheapest: TripOption | null;
  closest: TripOption | null;
  ranked: TripOption[];
};

/** One leg of a trip, for drawing: path is [[lat, lng], ...]. */
export type RouteLeg = { minutes: number; metres: number; path: [number, number][] };

export type TripRoute = {
  lot: { lot_id: number; lot_name: string; zone: string; centre: [number, number]; directions_url: string };
  drive: RouteLeg | null;
  walk: RouteLeg | null;
};

/** GET /api/lots: every lot outline as GeoJSON. */
export type LotsGeoJson = {
  type: "FeatureCollection";
  features: {
    type: "Feature";
    geometry: { type: "Polygon" | "MultiPolygon"; coordinates: unknown };
    properties: { id: number; name: string; zone: string; status: string };
  }[];
};

/** Where a trip starts and/or ends: a class building, the user's location, or both. */
export type TripQuery = { buildingId?: number | null; location?: { lat: number; lng: number } | null; hour?: number };
