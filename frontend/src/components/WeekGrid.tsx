// The Mon-Fri week grid. Class blocks are placed from their start and end times;
// the grid stretches past 8 am-5 pm when a class is earlier or later.
import { type DraftClass, DAY_NAMES, formatTime, gridHours, gridPosition, reviewNote, WEEKDAYS } from "../lib/schedule";

type Props = {
  classes: DraftClass[];
  selectedKey?: string | null;
  onSelect?: (item: DraftClass) => void;
  /** When set, clicking an empty slot adds a class there (day is ISO, start is "HH:MM"). */
  onAddAt?: (day: number, start: string) => void;
};

export function WeekGrid({ classes, selectedKey, onSelect, onAddAt }: Props) {
  const { first, last } = gridHours(classes);
  const hours = Array.from({ length: last - first }, (_, index) => first + index);
  const slots = hours.length * 4;                               // 15-minute slots

  return (
    <div className="week-grid" role="grid" aria-label="Class schedule">
      <div className="grid-corner" />
      {WEEKDAYS.map((day) => <div className="grid-day" key={day}>{DAY_NAMES[day]}</div>)}
      <div className="time-column" style={{ gridTemplateRows: `repeat(${hours.length}, 1fr)` }}>
        {hours.map((hour) => <span key={hour}>{formatTime(`${hour}:00`).replace(":00", "")}</span>)}
      </div>
      {WEEKDAYS.map((day) => (
        <div className="day-column" key={day} style={{ gridTemplateRows: `repeat(${slots}, 1fr)` }}>
          {Array.from({ length: slots }).map((_, index) => {
            const minutes = first * 60 + index * 15;
            const start = `${String(Math.floor(minutes / 60)).padStart(2, "0")}:${String(minutes % 60).padStart(2, "0")}`;
            return (
              <button
                key={index}
                className="grid-cell"
                aria-label={`${DAY_NAMES[day]}, ${formatTime(start)}`}
                onClick={() => onAddAt?.(day, start)}
              />
            );
          })}
          {classes.filter((item) => item.days.includes(day)).map((item) => {
            const note = reviewNote(item);
            return (
              <button
                key={`${item.key}-${day}`}
                className={["class-block", note ? "unsure" : "", item.include ? "" : "excluded",
                            item.key === selectedKey ? "selected" : ""].join(" ")}
                style={gridPosition(item, first, last)}
                onClick={() => onSelect?.(item)}
                aria-label={`${DAY_NAMES[day]}, ${formatTime(item.start)} to ${formatTime(item.end)}, ${item.course}`}
              >
                <span>{formatTime(item.start)}</span>
                <strong>{item.course}</strong>
                {note && <em>{note}</em>}
              </button>
            );
          })}
        </div>
      ))}
    </div>
  );
}
