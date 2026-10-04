// The Map page: pick one of your class buildings and/or use your location, and see where to park.
//
//   class building only      → lots ranked by walk to class
//   "Use my location" only   → lots ranked by drive from you
//   both                     → the whole trip: drive there, then walk to class
//
// The suggested lot's route is drawn on the map (solid = drive, dashed = walk).
import { useEffect, useMemo, useState } from "react";

import { ApiRequestError, getLots, getRecommendations, getRoute, listClasses } from "../api/client";
import type { LotsGeoJson, Priority, Recommendations, TripOption, TripRoute } from "../api/types";
import { ParkingMap } from "../components/ParkingMap";
import { Button, Heading, Icon, ZonePlate } from "../components/ui";
import { currentLocation, type LatLng } from "../lib/location";
import { formatTime } from "../lib/schedule";

const PRIORITIES: { value: Priority; label: string }[] = [
  { value: "best", label: "Best" },
  { value: "cheapest", label: "Cheapest" },
  { value: "closest", label: "Closest" },
];
const HOURS = Array.from({ length: 15 }, (_, index) => index + 7);   // 7 am - 9 pm (enforcement ends 10 pm)
const dollars = (cents: number) => `$${(cents / 100).toFixed(2)}`;

/** "drive 4 min · walk 6 min" for whichever legs this trip has */
function legs(option: TripOption): string {
  const parts = [];
  if (option.drive_min != null) parts.push(`drive ${option.drive_min} min`);
  if (option.walk_min != null) parts.push(`${option.walk_source === "estimate" ? "~" : ""}walk ${option.walk_min} min`);
  return parts.join(" · ");
}

export function MapPage({ defaultPriority }: { defaultPriority: Priority }) {
  const [buildings, setBuildings] = useState<{ id: number; name: string }[]>([]);
  const [buildingId, setBuildingId] = useState<number | null>(null);
  const [me, setMe] = useState<LatLng | null>(null);
  const [locating, setLocating] = useState(false);
  // null = let the API choose: the next class at this building, arriving 20 min early (the reminders' rule)
  const [hour, setHour] = useState<number | null>(null);
  const [priority, setPriority] = useState<Priority>(defaultPriority);
  const [recs, setRecs] = useState<Recommendations | null>(null);
  const [selectedLotId, setSelectedLotId] = useState<number | null>(null);
  const [route, setRoute] = useState<TripRoute | null>(null);
  const [lots, setLots] = useState<LotsGeoJson | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Once: the lot outlines, and the buildings your saved classes are in
  useEffect(() => {
    getLots().then(setLots).catch(() => setLots(null));
    listClasses().then((saved) => {
      const unique = new Map<number, string>();
      for (const item of saved) if (item.building_id && item.building_name) unique.set(item.building_id, item.building_name);
      const list = [...unique].map(([id, name]) => ({ id, name }));
      setBuildings(list);
      setBuildingId((current) => current ?? list[0]?.id ?? null);
    }).catch(() => setBuildings([]));
  }, []);

  // Whenever the trip changes, ask the API for lots, then select the pick for the chosen priority
  useEffect(() => {
    if (buildingId == null && !me) {
      setRecs(null);
      return;
    }
    setLoading(true);
    setError(null);
    getRecommendations({ buildingId, location: me, hour: hour ?? undefined })
      .then(setRecs)
      .catch((problem) => setError(problem instanceof ApiRequestError ? problem.message : "Couldn't load parking."))
      .finally(() => setLoading(false));
  }, [buildingId, me, hour]);

  useEffect(() => setSelectedLotId(recs?.[priority]?.lot_id ?? null), [recs, priority]);

  // The selected lot's route shape (cached on the server, so re-selecting is free)
  useEffect(() => {
    if (selectedLotId == null || (buildingId == null && !me)) {
      setRoute(null);
      return;
    }
    getRoute(selectedLotId, { buildingId, location: me }).then(setRoute).catch(() => setRoute(null));
  }, [selectedLotId, buildingId, me]);

  const useMyLocation = async () => {
    setLocating(true);
    setError(null);
    try {
      setMe(await currentLocation());
    } catch (problem) {
      setError((problem as Error).message);
    } finally {
      setLocating(false);
    }
  };

  // Lots shown solid on the map: every lot the API says this user may use at that hour
  const allowedLotIds = useMemo(() => new Set(recs?.allowed_lot_ids ?? []), [recs]);
  const selected = [recs?.best, recs?.cheapest, recs?.closest, ...(recs?.ranked ?? [])]
    .find((option) => option?.lot_id === selectedLotId) ?? null;
  // A chip is lit only while the selected lot is that pick, so clicking another lot can't look like "Best"
  const isPick = (value: Priority) => priority === value && recs?.[value]?.lot_id === selectedLotId;
  const pickLabel = (["best", "cheapest", "closest"] as Priority[]).find((value) => recs?.[value]?.lot_id === selectedLotId);
  const note = (option: TripOption) => (option.access_note ? ` · ${option.access_note}` : "");   // from the API
  const arrival = recs?.arrival;
  const buildingName = buildings.find((b) => b.id === buildingId)?.name;

  return (
    <div className="map-page">
      <aside className="map-sidebar">
        <span className="eyebrow">{arrival ? `Arriving around ${formatTime(`${arrival.hour}:00`)}` : "Plan your parking"}</span>
        <Heading>Find parking</Heading>
        <p>{me && buildingName ? `From your location to ${buildingName}.`
            : me ? "Near your location." : buildingName ? `Near ${buildingName}.` : "Pick a class building or use your location."}
          {arrival?.reason === "next class" && arrival.date && arrival.start && <><br /><small>For your next class there: {arrival.course},{" "}
            {new Date(`${arrival.date}T00:00`).toLocaleDateString("en-US", { weekday: "short" })} {formatTime(arrival.start)}</small></>}</p>

        <div className="map-controls">
          <label className="field">
            <span>Class building</span>
            <select value={buildingId ?? ""} onChange={(event) => setBuildingId(event.target.value ? Number(event.target.value) : null)}>
              <option value="">No building (location only)</option>
              {buildings.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
            </select>
          </label>
          <label className="field">
            <span>Arriving at</span>
            <select value={hour ?? ""} onChange={(event) => setHour(event.target.value ? Number(event.target.value) : null)}>
              <option value="">{buildingId != null ? "Next class (auto)" : "Now (auto)"}</option>
              {HOURS.map((h) => <option key={h} value={h}>{formatTime(`${h}:00`)}</option>)}
            </select>
          </label>
        </div>
        <Button variant="secondary" icon="location" className="full-button" onClick={me ? () => setMe(null) : useMyLocation} disabled={locating}>
          {locating ? "Finding you…" : me ? "Stop using my location" : "Use my location"}
        </Button>
        {recs?.far_from_campus && <p className="map-note">You're far from campus, so drive times are long. They're still real.</p>}
        {error && <p className="form-error" role="alert">{error}</p>}

        {recs && (
          <>
            <div className="filter-chips map-filters" role="radiogroup" aria-label="Parking priority">
              {PRIORITIES.map((item) => (
                <button key={item.value} role="radio" aria-checked={isPick(item.value)}
                        className={isPick(item.value) ? "active" : ""}
                        onClick={() => { setPriority(item.value); setSelectedLotId(recs[item.value]?.lot_id ?? null); }}>
                  {item.label}
                </button>
              ))}
            </div>
            {selected && (
              <div className="pick-card">
                <div className="lot-title">
                  <ZonePlate zone={selected.zone} large />
                  <span>
                    <em className="pick-label">{pickLabel ? `${pickLabel[0].toUpperCase()}${pickLabel.slice(1)} for you` : "You picked"}</em>
                    <strong>{selected.lot_name} · zone {selected.zone}</strong>
                    <small>{legs(selected)}{note(selected)}{route ? "" : " · loading route…"}</small>
                  </span>
                  <b>{dollars(selected.price_cents)}</b>
                </div>
                {selected.over_walk_limit &&
                  <small className="limit-note">Longer than your {recs.walk_limit_min}-min walk limit</small>}
                {selected.saves_cents > 0 && <span className="savings-pill">Saves {dollars(selected.saves_cents)} vs {recs.closest?.lot_name}</span>}
                <a className="directions-link" href={selected.directions_url} target="_blank" rel="noopener">
                  <Icon name="location" size={16} /> Directions in Google Maps
                </a>
              </div>
            )}
            <div className="ranked-lots">
              {recs.ranked.map((option, index) => (
                <button key={option.lot_id} className={`ranked-lot ${option.lot_id === selectedLotId ? "selected" : ""}`}
                        onClick={() => setSelectedLotId(option.lot_id)}>
                  <span className="rank">{index + 1}</span>
                  <ZonePlate zone={option.zone} large />
                  <span><strong>{option.lot_name}</strong><small>{legs(option)}{note(option)}</small></span>
                  <b>{dollars(option.price_cents)}</b>
                </button>
              ))}
            </div>
          </>
        )}
        {loading && <p className="loading-note">Finding parking…</p>}
        {!recs && !loading && buildings.length === 0 && !me &&
          <p className="map-note">Save your schedule with buildings, or use your location, to see parking.</p>}
      </aside>

      <div className="map-wrap">
        <ParkingMap lots={lots} allowedLotIds={allowedLotIds} selectedLotId={selectedLotId}
                    building={recs?.building && recs.building_centre ? { name: recs.building, centre: recs.building_centre } : null}
                    me={me} route={route} onLotClick={setSelectedLotId} />
        <div className="map-legend">
          <strong>Student prices</strong>
          <span><i className="scale l" /> L · $3.75</span>
          <span><i className="scale c" /> C · $5.50</span>
          <span><i className="scale cp" /> C+ · $6.50</span>
          <span><i className="scale route-drive" /> drive</span>
          <span><i className="scale route-walk" /> walk</span>
        </div>
      </div>
    </div>
  );
}
