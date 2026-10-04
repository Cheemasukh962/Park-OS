// The campus map (Leaflet + OpenStreetMap streets, free, no key).
//
// Leaflet isn't a React library: it owns its own <div> and changes the page itself. So this component
// creates the map once (first useEffect), keeps it in a ref, and in later effects swaps whole layers
// (lot outlines, pins, route lines) whenever their data changes.
import "leaflet/dist/leaflet.css";

import L from "leaflet";
import { useEffect, useRef } from "react";

import type { LotsGeoJson, TripRoute } from "../api/types";
import { CAMPUS_CENTRE, type LatLng } from "../lib/location";
import { zoneColour } from "../lib/zones";

type Props = {
  lots: LotsGeoJson | null;
  allowedLotIds: Set<number>;                 // lots this user may park in now: drawn solid, the rest faded
  selectedLotId: number | null;
  building: { name: string; centre: [number, number] } | null;
  me: LatLng | null;
  route: TripRoute | null;
  onLotClick: (lotId: number) => void;
};

export function ParkingMap({ lots, allowedLotIds, selectedLotId, building, me, route, onLotClick }: Props) {
  const host = useRef<HTMLDivElement>(null);
  const map = useRef<L.Map | null>(null);
  const layers = useRef<{ lots?: L.Layer; pins?: L.Layer; route?: L.Layer }>({});
  const clickHandler = useRef(onLotClick);
  clickHandler.current = onLotClick;          // always call the latest handler without redrawing the lots

  // 1. Create the map once
  useEffect(() => {
    if (!host.current) return;
    const created = L.map(host.current).setView([CAMPUS_CENTRE.lat, CAMPUS_CENTRE.lng], 15);
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(created);
    map.current = created;
    return () => {
      created.remove();                       // leaving the page: free the map
      map.current = null;
    };
  }, []);

  // Swap one named layer for a new one
  const replace = (name: keyof typeof layers.current, layer: L.Layer | undefined) => {
    layers.current[name]?.remove();
    layers.current[name] = layer;
    if (layer && map.current) layer.addTo(map.current);
  };

  // 2. Lot outlines, coloured by zone; allowed lots solid, others faded; the selected lot outlined in gold
  useEffect(() => {
    if (!lots) return;
    replace("lots", L.geoJSON(lots as GeoJSON.FeatureCollection, {
      style: (feature) => {
        const { id, zone } = feature?.properties ?? {};
        const allowed = allowedLotIds.has(id);
        return {
          color: id === selectedLotId ? "#ffbf00" : "#022851",
          weight: id === selectedLotId ? 4 : 1,
          fillColor: zoneColour(zone),
          fillOpacity: allowed ? 0.75 : 0.18,
          opacity: allowed || id === selectedLotId ? 1 : 0.3,
        };
      },
      onEachFeature: (feature, layer) => {
        const { id, name, zone } = feature.properties;
        layer.bindTooltip(`${name} · ${zone === "?" ? "no zone" : `zone ${zone}`}`, { sticky: true });
        if (allowedLotIds.has(id)) layer.on("click", () => clickHandler.current(id));
      },
    }));
  }, [lots, allowedLotIds, selectedLotId]);

  // 3. Pins: the class building (navy) and the user's location (gold). Circles, so no image files are needed
  useEffect(() => {
    const pins = L.layerGroup();
    if (building) {
      L.circleMarker(building.centre, { radius: 9, color: "white", weight: 3, fillColor: "#022851", fillOpacity: 1 })
        .bindTooltip(building.name, { permanent: true, direction: "top", offset: [0, -10] }).addTo(pins);
    }
    if (me) {
      L.circleMarker([me.lat, me.lng], { radius: 9, color: "white", weight: 3, fillColor: "#ffbf00", fillOpacity: 1 })
        .bindTooltip("You", { permanent: true, direction: "top", offset: [0, -10] }).addTo(pins);
    }
    replace("pins", pins);
  }, [building, me]);

  // 4. The trip: drive as a solid line, walk dashed. Then zoom to fit everything that matters
  useEffect(() => {
    const group = L.layerGroup();
    if (route?.drive) L.polyline(route.drive.path, { color: "#022851", weight: 5, opacity: 0.85 }).addTo(group);
    if (route?.walk) L.polyline(route.walk.path, { color: "#13639e", weight: 4, dashArray: "6 8" }).addTo(group);
    replace("route", group);

    const points: L.LatLngExpression[] = [
      ...(route?.drive?.path ?? []), ...(route?.walk?.path ?? []),
      ...(building ? [building.centre] : []), ...(me ? [[me.lat, me.lng] as [number, number]] : []),
    ];
    if (route?.lot) points.push(route.lot.centre);
    if (points.length > 1) map.current?.fitBounds(L.latLngBounds(points), { padding: [50, 50], maxZoom: 17 });
    else if (points.length === 1) map.current?.setView(points[0], 16);
  }, [route, building, me]);

  return <div ref={host} className="campus-map leaflet-host" aria-label="Map of campus parking" />;
}
