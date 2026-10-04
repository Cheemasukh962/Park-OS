// Type-ahead building search: type "well" → pick Wellman Hall from /api/buildings.
import { useEffect, useState } from "react";

import { searchBuildings } from "../api/client";
import type { Building } from "../api/types";

type Props = {
  label?: string;
  value: { id: number | null; name: string | null };
  onChange: (building: Building | null) => void;
};

export function BuildingPicker({ label = "Building (optional)", value, onChange }: Props) {
  const [query, setQuery] = useState(value.name ?? "");
  const [results, setResults] = useState<Building[]>([]);
  const [open, setOpen] = useState(false);

  // Show the chosen building's name when a different class is selected
  useEffect(() => setQuery(value.name ?? ""), [value.id, value.name]);

  // Search as the user types, waiting 200 ms after the last key so we don't send a request per letter
  useEffect(() => {
    if (!open || query.trim().length < 2) {
      setResults([]);
      return;
    }
    const timer = setTimeout(() => {
      searchBuildings(query).then(setResults).catch(() => setResults([]));
    }, 200);
    return () => clearTimeout(timer);                         // typing again cancels the previous wait
  }, [query, open]);

  return (
    <label className="field building-picker">
      <span>{label}</span>
      <input
        value={query}
        placeholder="Search buildings"
        onFocus={() => setOpen(true)}
        onBlur={() => setTimeout(() => setOpen(false), 150)}   // let a click on a result land first
        onChange={(event) => {
          setQuery(event.target.value);
          if (!event.target.value) onChange(null);
        }}
      />
      {open && results.length > 0 && (
        <ul className="picker-results" role="listbox">
          {results.map((building) => (
            <li key={building.id}>
              <button
                type="button"
                onMouseDown={(event) => event.preventDefault()}   // keep focus so onBlur doesn't close first
                onClick={() => {
                  onChange(building);
                  setQuery(building.name);
                  setOpen(false);
                }}
              >
                <strong>{building.name}</strong>
                <small>{building.category}</small>
              </button>
            </li>
          ))}
        </ul>
      )}
    </label>
  );
}
