// Map colours per parking zone, matching the design's legend (lighter = cheaper for students).
export const ZONE_COLOURS: Record<string, string> = {
  L: "#cce0f3",       // $3.75
  C: "#73abdd",       // $5.50
  "C+": "#13639e",    // $6.50
  A: "#022851",       // $6.50, students after 5 pm only
};
export const NO_ZONE_COLOUR = "#b8c2cc";   // Misc. lots: price unknown, never recommended

export const zoneColour = (zone: string) => ZONE_COLOURS[zone] ?? NO_ZONE_COLOUR;
