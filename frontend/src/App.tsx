import { ChangeEvent, ReactNode, useMemo, useState } from "react";

type Screen =
  | "welcome"
  | "login"
  | "role"
  | "method"
  | "upload"
  | "grid"
  | "buildings"
  | "edit-reminders"
  | "week"
  | "schedule"
  | "map"
  | "settings";

type IconName =
  | "arrow-left"
  | "arrow-right"
  | "calendar"
  | "check"
  | "chevron"
  | "clock"
  | "gear"
  | "grid"
  | "location"
  | "mail"
  | "map"
  | "more"
  | "plus"
  | "upload"
  | "user";

type ClassItem = {
  course: string;
  days: number[];
  start: string;
  end: string;
  building: string;
  top: number;
  height: number;
  unsure?: boolean;
};

const colors = {
  navy: "#022851",
  blue: "#13639E",
  gold: "#FFBF00",
};

const initialClasses: ClassItem[] = [
  {
    course: "ECS 36A",
    days: [0, 2, 4],
    start: "10:00 am",
    end: "10:50 am",
    building: "Olson Hall",
    top: 18.75,
    height: 10.4,
  },
  {
    course: "MAT 21C",
    days: [1, 3],
    start: "12:10 pm",
    end: "1:30 pm",
    building: "California Hall",
    top: 45.1,
    height: 16.6,
  },
  {
    course: "DES 001",
    days: [0, 2],
    start: "2:10 pm",
    end: "3:30 pm",
    building: "",
    top: 70.1,
    height: 16.6,
  },
];

const days = ["Mon", "Tue", "Wed", "Thu", "Fri"];
const times = ["8 am", "9 am", "10 am", "11 am", "12 pm", "1 pm", "2 pm", "3 pm", "4 pm"];

function Icon({ name, size = 20 }: { name: IconName; size?: number }) {
  const paths: Record<IconName, ReactNode> = {
    "arrow-left": <path d="m15 18-6-6 6-6" />,
    "arrow-right": <path d="m9 18 6-6-6-6" />,
    calendar: (
      <>
        <rect x="3" y="5" width="18" height="16" rx="2" />
        <path d="M16 3v4M8 3v4M3 10h18" />
      </>
    ),
    check: <path d="m5 12 4 4L19 6" />,
    chevron: <path d="m9 18 6-6-6-6" />,
    clock: (
      <>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 7v5l3 2" />
      </>
    ),
    gear: (
      <>
        <circle cx="12" cy="12" r="3" />
        <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-2.8 2.8-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6v.2h-4V21a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1L4.2 17l.1-.1a1.7 1.7 0 0 0 .3-1.9A1.7 1.7 0 0 0 3 14H2.8v-4H3a1.7 1.7 0 0 0 1.6-1 1.7 1.7 0 0 0-.3-1.9L4.2 7 7 4.2l.1.1A1.7 1.7 0 0 0 9 4.6 1.7 1.7 0 0 0 10 3V2.8h4V3a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1L19.8 7l-.1.1a1.7 1.7 0 0 0-.3 1.9 1.7 1.7 0 0 0 1.6 1h.2v4H21a1.7 1.7 0 0 0-1.6 1Z" />
      </>
    ),
    grid: (
      <>
        <rect x="3" y="3" width="7" height="7" rx="1" />
        <rect x="14" y="3" width="7" height="7" rx="1" />
        <rect x="3" y="14" width="7" height="7" rx="1" />
        <rect x="14" y="14" width="7" height="7" rx="1" />
      </>
    ),
    location: (
      <>
        <path d="M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0Z" />
        <circle cx="12" cy="10" r="2.5" />
      </>
    ),
    mail: (
      <>
        <rect x="3" y="5" width="18" height="14" rx="2" />
        <path d="m4 7 8 6 8-6" />
      </>
    ),
    map: (
      <>
        <path d="m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3Z" />
        <path d="M9 3v15M15 6v15" />
      </>
    ),
    more: (
      <>
        <circle cx="5" cy="12" r="1" fill="currentColor" stroke="none" />
        <circle cx="12" cy="12" r="1" fill="currentColor" stroke="none" />
        <circle cx="19" cy="12" r="1" fill="currentColor" stroke="none" />
      </>
    ),
    plus: <path d="M12 5v14M5 12h14" />,
    upload: (
      <>
        <path d="M12 16V4M7 9l5-5 5 5" />
        <path d="M5 14v5h14v-5" />
      </>
    ),
    user: (
      <>
        <circle cx="12" cy="8" r="4" />
        <path d="M4 21a8 8 0 0 1 16 0" />
      </>
    ),
  };
  return (
    <svg
      aria-hidden="true"
      className="icon"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {paths[name]}
    </svg>
  );
}

function Button({
  children,
  variant = "primary",
  icon,
  onClick,
  type = "button",
  disabled,
  className = "",
}: {
  children: ReactNode;
  variant?: "primary" | "secondary" | "ghost";
  icon?: IconName;
  onClick?: () => void;
  type?: "button" | "submit";
  disabled?: boolean;
  className?: string;
}) {
  return (
    <button
      type={type}
      className={`button button-${variant} ${className}`}
      onClick={onClick}
      disabled={disabled}
    >
      {icon && <Icon name={icon} size={18} />}
      {children}
    </button>
  );
}

function Heading({
  level = 1,
  children,
  className = "",
}: {
  level?: 1 | 2 | 3;
  children: ReactNode;
  className?: string;
}) {
  const Tag = `h${level}` as "h1" | "h2" | "h3";
  return <Tag className={`heading heading-${level} ${className}`}>{children}</Tag>;
}

function Field({
  label,
  value,
  placeholder,
  type = "text",
  onChange,
}: {
  label: string;
  value?: string;
  placeholder?: string;
  type?: string;
  onChange?: (value: string) => void;
}) {
  return (
    <label className="field">
      <span>{label}</span>
      <input
        type={type}
        value={value}
        placeholder={placeholder}
        onChange={(event) => onChange?.(event.target.value)}
      />
    </label>
  );
}

function Logo({ compact = false }: { compact?: boolean }) {
  return (
    <div className="logo" aria-label="ParkOS">
      <span className="logo-mark"><span>P</span></span>
      {!compact && <strong>ParkOS</strong>}
    </div>
  );
}

function ZonePlate({ zone, large = false }: { zone: string; large?: boolean }) {
  return <span className={`zone-plate ${large ? "zone-large" : ""}`}>{zone}</span>;
}

function StepIndicator({ step }: { step: number }) {
  return (
    <div className="step-indicator">
      <span>Step {step} of 4</span>
      <div className="step-bars" aria-hidden="true">
        {[1, 2, 3, 4].map((item) => (
          <span key={item} className={item <= step ? "complete" : ""} />
        ))}
      </div>
    </div>
  );
}

function OnboardingShell({
  step,
  onBack,
  children,
}: {
  step: number;
  onBack: () => void;
  children: ReactNode;
}) {
  return (
    <div className="onboarding-shell">
      <header className="onboarding-header">
        <Logo />
        <StepIndicator step={step} />
        <Button variant="ghost" onClick={onBack}>Back</Button>
      </header>
      <main className="onboarding-content">{children}</main>
    </div>
  );
}

function Ticket({ className = "" }: { className?: string }) {
  return (
    <div className={`ticket ${className}`} aria-hidden="true">
      <div className="ticket-top"><span>NOTICE</span><b>$</b></div>
      <div className="ticket-line long" />
      <div className="ticket-line" />
      <div className="ticket-line short" />
      <div className="ticket-code">PARKING CITATION</div>
    </div>
  );
}

function Welcome({ onStart }: { onStart: () => void }) {
  return (
    <main className="welcome">
      <header className="welcome-header"><Logo /></header>
      <section className="welcome-inner">
        <div className="welcome-copy">
          <span className="eyebrow">Your campus parking co-pilot</span>
          <Heading className="display">No more parking tickets.</Heading>
          <p className="welcome-subline">
            ParkOS emails you before your first class each weekday and shows the
            cheapest lot you're allowed to use.
          </p>
          <div className="welcome-actions">
            <Button onClick={onStart}>Get started <Icon name="arrow-right" /></Button>
            <span>For UC Davis students, staff and visitors.</span>
          </div>
        </div>
        <div className="hero-art" aria-hidden="true">
          <Ticket className="ticket-1" />
          <Ticket className="ticket-2" />
          <Ticket className="ticket-3" />
          <Ticket className="ticket-4" />
          <Ticket className="ticket-main" />
          <div className="no-parking"><span /></div>
          <div className="hero-note">Save the citation for your wall, not your windshield.</div>
        </div>
      </section>
      <footer className="welcome-footer">
        <span>Built for campus days</span>
        <span>Parking reminders · lot comparisons · weekly planning</span>
      </footer>
    </main>
  );
}

function Login({
  onContinue,
  onBack,
}: {
  onContinue: () => void;
  onBack: () => void;
}) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  return (
    <main className="login-page">
      <header className="login-header">
        <Logo />
        <Button variant="ghost" onClick={onBack}>
          Back to home
        </Button>
      </header>
      <section className="login-layout">
        <div className="login-intro">
          <span className="eyebrow">Welcome back</span>
          <Heading className="login-title">Your parking plan is waiting.</Heading>
          <p>
            Sign in to see your schedule, reminders, and the best place to park
            before class.
          </p>
          <div className="login-ticket-wrap" aria-hidden="true">
            <Ticket className="login-ticket" />
            <div className="login-symbol"><span /></div>
          </div>
        </div>
        <form
          className="login-card"
          onSubmit={(event) => {
            event.preventDefault();
            onContinue();
          }}
        >
          <div className="login-card-heading">
            <Heading level={2}>Sign in to ParkOS</Heading>
            <p>Use your account details to continue.</p>
          </div>
          <Field
            label="Email address"
            type="email"
            value={email}
            placeholder="student@ucdavis.edu"
            onChange={setEmail}
          />
          <Field
            label="Password"
            type="password"
            value={password}
            placeholder="Enter your password"
            onChange={setPassword}
          />
          <div className="login-options">
            <label className="remember-me">
              <input type="checkbox" />
              <span>Keep me signed in</span>
            </label>
            <button type="button" className="text-button">Forgot password?</button>
          </div>
          <Button type="submit" className="full-button">
            Sign in <Icon name="arrow-right" />
          </Button>
          <div className="login-divider"><span>New to ParkOS?</span></div>
          <Button variant="secondary" className="full-button" onClick={onContinue}>
            Create an account
          </Button>
          <p className="demo-note">
            Front-end preview: any email and password will continue.
          </p>
        </form>
      </section>
    </main>
  );
}

function RoleStep({ next, back }: { next: () => void; back: () => void }) {
  const roles = [
    ["Student", "Cheapest lots for you. A zone after 5 pm only.", "user"],
    ["Staff or faculty", "Every zone is open to you.", "calendar"],
    ["Visitor", "$19.00 in every zone, so we'll show the closest lot.", "location"],
  ] as const;
  return (
    <OnboardingShell step={1} onBack={back}>
      <div className="step-heading">
        <span className="eyebrow">First, a quick question</span>
        <Heading>Who are you?</Heading>
        <p>Parking access changes by affiliation. Pick the one that fits.</p>
      </div>
      <div className="choice-grid" role="radiogroup" aria-label="Affiliation">
        {roles.map(([title, copy, icon]) => (
          <button key={title} className="choice-card" role="radio" aria-checked="false" onClick={next}>
            <span className="choice-icon"><Icon name={icon} size={24} /></span>
            <span>
              <strong>{title}</strong>
              <small>{copy}</small>
            </span>
            <Icon name="chevron" />
          </button>
        ))}
      </div>
      <p className="privacy-note">You can change this later in Settings.</p>
    </OnboardingShell>
  );
}

function MethodStep({
  select,
  back,
}: {
  select: (screen: Screen) => void;
  back: () => void;
}) {
  return (
    <OnboardingShell step={2} onBack={back}>
      <div className="step-heading">
        <span className="eyebrow">Build your week</span>
        <Heading>Add your classes</Heading>
        <p>Choose the quickest way to bring in your schedule.</p>
      </div>
      <div className="method-grid">
        <button className="method-card" onClick={() => select("upload")}>
          <span className="method-illustration upload-illustration">
            <Icon name="upload" size={32} />
            <i className="file file-one">PDF</i>
            <i className="file file-two">JPG</i>
          </span>
          <span>
            <strong>Upload your schedule</strong>
            <small>Screenshot, photo, PDF or calendar file</small>
          </span>
          <span className="card-link">Choose a file <Icon name="arrow-right" size={16} /></span>
        </button>
        <button className="method-card" onClick={() => select("grid")}>
          <span className="method-illustration grid-illustration">
            <span className="mini-grid">
              {Array.from({ length: 20 }).map((_, index) => <i key={index} className={[6, 7, 11, 12, 13].includes(index) ? "filled" : ""} />)}
            </span>
          </span>
          <span>
            <strong>Fill it in yourself</strong>
            <small>Drag over your class times on a week grid</small>
          </span>
          <span className="card-link">Open the grid <Icon name="arrow-right" size={16} /></span>
        </button>
      </div>
      <Button variant="ghost" icon="plus" onClick={() => select("grid")}>Add one class at a time instead</Button>
    </OnboardingShell>
  );
}

function UploadStep({
  back,
  review,
}: {
  back: () => void;
  review: () => void;
}) {
  const [fileName, setFileName] = useState("");
  const chooseFile = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) setFileName(file.name);
  };
  return (
    <OnboardingShell step={2} onBack={back}>
      <div className="step-heading">
        <span className="eyebrow">Schedule import</span>
        <Heading>Upload your schedule</Heading>
        <p>We'll read your classes and put them on the grid for you to check.</p>
      </div>
      <label className={`drop-zone ${fileName ? "has-file" : ""}`}>
        <input
          type="file"
          accept=".png,.jpg,.jpeg,.heic,.pdf,.ics"
          onChange={chooseFile}
        />
        <span className="drop-icon"><Icon name={fileName ? "check" : "upload"} size={28} /></span>
        <strong>{fileName || "Drop your schedule here"}</strong>
        <small>{fileName ? "Ready to read your schedule" : "PNG, JPG, HEIC, PDF or ICS · up to 10 MB"}</small>
        <span className="button button-secondary">{fileName ? "Choose a different file" : "Choose file"}</span>
      </label>
      <div className="upload-footer">
        <Button variant="ghost" onClick={() => review()}>Fill it in myself</Button>
        <Button onClick={review} disabled={!fileName}>Read my schedule</Button>
      </div>
    </OnboardingShell>
  );
}

function WeekGrid({
  editable = false,
  onSelect,
}: {
  editable?: boolean;
  onSelect?: (item: ClassItem) => void;
}) {
  return (
    <div className="week-grid" role="grid" aria-label="Class schedule">
      <div className="grid-corner" />
      {days.map((day) => <div className="grid-day" key={day}>{day}</div>)}
      <div className="time-column">
        {times.map((time) => <span key={time}>{time}</span>)}
      </div>
      {days.map((day, dayIndex) => (
        <div className="day-column" key={day}>
          {Array.from({ length: 36 }).map((_, index) => (
            <button
              key={index}
              className="grid-cell"
              aria-label={`${day}, ${Math.floor(index / 4) + 8}:${(index % 4) * 15 || "00"}`}
              onClick={() => editable && onSelect?.({
                course: "New class",
                days: [dayIndex],
                start: "11:00 am",
                end: "12:00 pm",
                building: "",
                top: 37.5,
                height: 12.5,
              })}
            />
          ))}
          {initialClasses.filter((item) => item.days.includes(dayIndex)).map((item) => (
            <button
              key={`${item.course}-${day}`}
              className={`class-block ${item.unsure ? "unsure" : ""}`}
              style={{ top: `${item.top}%`, height: `${item.height}%` }}
              onClick={() => onSelect?.(item)}
              aria-label={`${day}, ${item.start} to ${item.end}, ${item.course}`}
            >
              <span>{item.start}</span>
              <strong>{item.course}</strong>
              {item.unsure && <em>Check this</em>}
            </button>
          ))}
        </div>
      ))}
    </div>
  );
}

function ClassPanel({
  item,
  onClose,
}: {
  item: ClassItem;
  onClose: () => void;
}) {
  const [course, setCourse] = useState(item.course === "New class" ? "" : item.course);
  const [building, setBuilding] = useState(item.building);
  return (
    <aside className="details-panel">
      <div className="panel-header">
        <div><span className="eyebrow">Class details</span><Heading level={2}>{item.course}</Heading></div>
        <button className="icon-button" onClick={onClose} aria-label="Close">×</button>
      </div>
      <Field label="Course" value={course} placeholder="ECS 36A" onChange={setCourse} />
      <div className="field">
        <span>Days</span>
        <div className="day-toggles">
          {days.map((day, index) => <button className={item.days.includes(index) ? "active" : ""} key={day} aria-pressed={item.days.includes(index)}>{day.slice(0, 1)}</button>)}
        </div>
      </div>
      <div className="field-row">
        <Field label="Starts" value={item.start.replace(" am", "").replace(" pm", "")} />
        <Field label="Ends" value={item.end.replace(" am", "").replace(" pm", "")} />
      </div>
      <p className="helper">Most UC Davis classes start at :00 or :10.</p>
      <Field label="Building (optional)" value={building} placeholder="Search buildings" onChange={setBuilding} />
      <button className="skip-link">Skip for now</button>
      <div className="panel-actions">
        <Button variant="ghost">Delete</Button>
        <Button onClick={onClose}>Save class</Button>
      </div>
    </aside>
  );
}

function GridStep({
  next,
  back,
}: {
  next: () => void;
  back: () => void;
}) {
  const [selected, setSelected] = useState<ClassItem | null>(initialClasses[0]);
  return (
    <OnboardingShell step={3} onBack={back}>
      <div className="grid-step-heading">
        <div>
          <span className="eyebrow">Your weekly rhythm</span>
          <Heading>Mark your class times</Heading>
          <p>Click any class to fine-tune its details, or click an empty time to add one.</p>
        </div>
        <label className="switch-label"><input type="checkbox" /><span /> Show weekend</label>
      </div>
      <div className="grid-workspace">
        <WeekGrid editable onSelect={setSelected} />
        {selected && <ClassPanel item={selected} onClose={() => setSelected(null)} />}
      </div>
      <div className="sticky-footer">
        <span><strong>3</strong> classes · 5 weekdays</span>
        <Button onClick={next}>Continue <Icon name="arrow-right" /></Button>
      </div>
    </OnboardingShell>
  );
}

function BuildingsStep({ next, back }: { next: () => void; back: () => void }) {
  return (
    <OnboardingShell step={4} onBack={back}>
      <div className="step-heading">
        <span className="eyebrow">Optional, but useful</span>
        <Heading>Where are your classes?</Heading>
        <p>It's how we find you cheaper parking. You can skip any class.</p>
      </div>
      <div className="building-list">
        {initialClasses.map((item) => (
          <div className="building-row" key={item.course}>
            <div className="course-summary">
              <span className="course-initial">{item.course.slice(0, 2)}</span>
              <span><strong>{item.course}</strong><small>{item.days.map((day) => days[day]).join(", ")} · {item.start}</small></span>
            </div>
            <Field label="Building" value={item.building} placeholder="Search buildings" />
            <Button variant="ghost">Skip</Button>
          </div>
        ))}
      </div>
      <div className="simple-footer">
        <span>You can add buildings later from your schedule.</span>
        <Button onClick={next}>Continue <Icon name="arrow-right" /></Button>
      </div>
    </OnboardingShell>
  );
}

function ReminderSettingsPage({
  onDone,
  remindersOn,
  setRemindersOn,
}: {
  onDone: () => void;
  remindersOn: boolean;
  setRemindersOn: (value: boolean) => void;
}) {
  const [timing, setTiming] = useState("-15");
  const [email, setEmail] = useState("student@ucdavis.edu");
  const reminderTimes: Record<string, string> = {
    "-15": "9:45",
    "-5": "9:55",
    "0": "10:00",
    "5": "10:05",
    "10": "10:10",
  };
  const timingOptions = [
    { value: "-15", label: "15 min early" },
    { value: "-5", label: "5 min early" },
    { value: "0", label: "On time" },
    { value: "5", label: "5 min later" },
    { value: "10", label: "10 min later" },
  ];
  return (
    <>
      <div className="page-header reminder-page-header">
        <div>
          <button className="back-link" onClick={onDone}><Icon name="arrow-left" size={17} /> This week</button>
          <span className="eyebrow">Reminder preferences</span>
          <Heading>Edit reminders</Heading>
          <p>Choose when ParkOS should nudge you before your first class.</p>
        </div>
        <div className="reminder-master">
          <span><strong>Daily reminders</strong><small>{remindersOn ? "On for class days" : "Currently off"}</small></span>
          <button className={`toggle ${remindersOn ? "on" : ""}`} role="switch" aria-checked={remindersOn} onClick={() => setRemindersOn(!remindersOn)}><span /></button>
        </div>
      </div>
      <div className="reminder-layout reminder-settings-layout">
        <div>
          <div className="reminder-form">
            <Field label="Email address" type="email" value={email} onChange={setEmail} />
            <div className="field">
              <span>When should we remind you?</span>
              <div className="timing-options" role="radiogroup" aria-label="Reminder timing">
                {timingOptions.map((option) => (
                  <button
                    type="button"
                    role="radio"
                    aria-checked={timing === option.value}
                    className={timing === option.value ? "active" : ""}
                    key={option.value}
                    onClick={() => setTiming(option.value)}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
              <small className="timing-helper">Timing is based on the start of your first class that day.</small>
            </div>
            <Button className="full-button" onClick={() => { setRemindersOn(true); onDone(); }}>Save reminder settings</Button>
          </div>
        </div>
        <div className="preview-card">
          <span className="eyebrow">Monday's preview</span>
          <div className="preview-icon"><Icon name="mail" size={28} /></div>
          <span className="preview-time">{reminderTimes[timing]} <small>am</small></span>
          <Heading level={2}>Time to think about parking.</Heading>
          <p>Your first class is ECS 36A at 10:00 am in Olson Hall.</p>
          <div className="preview-lot"><ZonePlate zone="L" /><span><strong>Lot 2 · $3.75</strong><small>About 10 min walk</small></span></div>
          <span className="savings-pill">Saves $2.75 vs Lot 5</span>
        </div>
      </div>
    </>
  );
}

const navItems: { screen: Screen; label: string; icon: IconName }[] = [
  { screen: "week", label: "This week", icon: "calendar" },
  { screen: "schedule", label: "Schedule", icon: "grid" },
  { screen: "map", label: "Map", icon: "map" },
  { screen: "settings", label: "Settings", icon: "gear" },
];

function AppShell({
  screen,
  navigate,
  remindersOn,
  children,
}: {
  screen: Screen;
  navigate: (screen: Screen) => void;
  remindersOn: boolean;
  children: ReactNode;
}) {
  return (
    <div className="app-shell">
      <header className="topbar">
        <Logo />
        <nav className="desktop-nav" aria-label="Main navigation">
          {navItems.map((item) => (
            <button key={item.screen} className={screen === item.screen ? "active" : ""} onClick={() => navigate(item.screen)}>
              {item.label}
            </button>
          ))}
        </nav>
        <div className="topbar-meta">
          <span className={`status-dot ${remindersOn ? "" : "off"}`}><i /> Reminders {remindersOn ? "on · 30 min" : "off"}</span>
          <span className="affiliation"><Icon name="user" size={16} /> Student</span>
        </div>
      </header>
      <main className="app-content">{children}</main>
      <nav className="mobile-nav" aria-label="Main navigation">
        {navItems.map((item) => (
          <button key={item.screen} className={screen === item.screen ? "active" : ""} onClick={() => navigate(item.screen)}>
            <Icon name={item.icon} size={20} /><span>{item.label}</span>
          </button>
        ))}
      </nav>
    </div>
  );
}

const dayData = [
  { day: "Mon", date: "Nov 2", time: "9:30", meridiem: "am", course: "ECS 36A", classTime: "10:00 am", building: "Olson Hall", status: "normal" },
  { day: "Tue", date: "Nov 3", time: "11:40", meridiem: "am", course: "MAT 21C", classTime: "12:10 pm", building: "California Hall", status: "normal" },
  { day: "Wed", date: "Nov 4", time: "9:30", meridiem: "am", course: "ECS 36A", classTime: "10:00 am", building: "Olson Hall", status: "normal" },
  { day: "Thu", date: "Nov 5", time: "11:40", meridiem: "am", course: "MAT 21C", classTime: "12:10 pm", building: "California Hall", status: "normal" },
  { day: "Fri", date: "Nov 6", status: "skipped", reason: "No classes" },
];

function DayCard({ data }: { data: (typeof dayData)[number] }) {
  const [filter, setFilter] = useState("Best");
  const lots: Record<string, { zone: string; lot: string; price: string; walk: number }> = {
    Best: { zone: "L", lot: "Lot 2", price: "$3.75", walk: 10 },
    Cheapest: { zone: "L", lot: "Lot 30", price: "$3.75", walk: 18 },
    Closest: { zone: "C+", lot: "Lot 5", price: "$6.50", walk: 2 },
  };
  if (data.status === "skipped") {
    return (
      <article className="day-card skipped">
        <div className="day-card-heading"><strong>{data.day}</strong><span>{data.date}</span></div>
        <div className="skipped-content"><Icon name="calendar" size={24} /><strong>{data.reason}</strong><span>Nothing to plan today.</span></div>
      </article>
    );
  }
  const lot = lots[filter];
  return (
    <article className="day-card">
      <div className="day-card-heading">
        <span><strong>{data.day}</strong> {data.date}</span>
        <button className="icon-button" aria-label={`More options for ${data.day}`}><Icon name="more" /></button>
      </div>
      <span className="overline">Reminder</span>
      <time className="big-time">{data.time} <small>{data.meridiem}</small></time>
      <p className="first-class"><strong>{data.course}</strong> at {data.classTime}<br /><span>{data.building}</span></p>
      <div className="filter-chips" role="radiogroup" aria-label="Parking priority">
        {Object.keys(lots).map((item) => <button role="radio" aria-checked={filter === item} className={filter === item ? "active" : ""} onClick={() => setFilter(item)} key={item}>{item}</button>)}
      </div>
      <div className="lot-result" key={filter}>
        <div className="lot-title"><ZonePlate zone={lot.zone} large /><span><strong>{lot.lot}</strong><small>{filter === "Best" ? "Suggested for you" : filter}</small></span></div>
        <div className="lot-numbers"><strong>{lot.price}</strong><span className={lot.walk > 10 ? "over-limit" : ""}>~{lot.walk} min walk</span></div>
        {filter !== "Closest" && <span className="savings-pill">Saves $2.75 vs Lot 5</span>}
      </div>
    </article>
  );
}

function WeekPage({
  remindersOn,
  setRemindersOn,
  editReminders,
}: {
  remindersOn: boolean;
  setRemindersOn: (value: boolean) => void;
  editReminders: () => void;
}) {
  const [sent, setSent] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  return (
    <>
      <div className="page-header">
        <div><span className="eyebrow">Your parking plan</span><Heading>This week</Heading><p>November 2–6, 2026</p></div>
        <div className="page-actions">
          <div className="week-arrows"><button aria-label="Previous week"><Icon name="arrow-left" /></button><button aria-label="Next week"><Icon name="arrow-right" /></button></div>
          <Button variant="secondary" icon={sent ? "check" : "mail"} onClick={() => setSent(true)}>{sent ? "Sent" : "Email me this week"}</Button>
          <div className="overflow-wrap">
            <button className="overflow-button" aria-label="This week options" aria-expanded={menuOpen} onClick={() => setMenuOpen(!menuOpen)}><Icon name="more" /></button>
            {menuOpen && (
              <div className="week-menu">
                <div className="menu-toggle-row">
                  <span><strong>Reminders</strong><small>{remindersOn ? "On for class days" : "Currently off"}</small></span>
                  <button className={`toggle ${remindersOn ? "on" : ""}`} role="switch" aria-checked={remindersOn} onClick={() => setRemindersOn(!remindersOn)}><span /></button>
                </div>
                <button className="menu-action" onClick={editReminders}><Icon name="clock" size={18} /><span><strong>Edit reminders</strong><small>Email and reminder timing</small></span><Icon name="chevron" size={16} /></button>
              </div>
            )}
          </div>
        </div>
      </div>
      {!remindersOn && <div className="reminders-banner"><span><strong>Reminders are off.</strong> Turn them on when you want a nudge before class.</span><Button variant="secondary" onClick={() => setRemindersOn(true)}>Turn on</Button></div>}
      <div className="summary-strip">
        <div><span className="summary-icon"><Icon name="clock" /></span><span><small>Next reminder</small><strong>Monday at 9:30 am</strong></span></div>
        <div><span className="summary-icon gold"><span>$</span></span><span><small>Potential weekly savings</small><strong>$11.00</strong></span></div>
        <p>Parking isn't enforced Saturday or Sunday.</p>
      </div>
      <div className="day-card-grid">{dayData.map((data) => <DayCard key={data.day} data={data} />)}</div>
    </>
  );
}

function SchedulePage() {
  const [selected, setSelected] = useState<ClassItem | null>(null);
  return (
    <>
      <div className="page-header">
        <div><span className="eyebrow">Fall quarter</span><Heading>Schedule</Heading><p>3 classes · 5 weekdays</p></div>
        <div className="page-actions"><Button variant="secondary" icon="upload">Upload schedule</Button><Button icon="plus" onClick={() => setSelected(initialClasses[0])}>Add class</Button></div>
      </div>
      <div className="schedule-shell">
        <div className="schedule-grid-card">
          <div className="schedule-note"><span>Week of Nov 2</span><span><i className="legend-block" /> Your classes</span></div>
          <WeekGrid onSelect={setSelected} />
        </div>
        <aside className="schedule-aside">
          <span className="eyebrow">Quick check</span>
          <Heading level={2}>1 class needs a building</Heading>
          <p>Add a building to DES 001 for parking tips on Monday and Wednesday.</p>
          <Button variant="secondary">Add building</Button>
        </aside>
      </div>
      {selected && <div className="panel-overlay" onClick={() => setSelected(null)}><div onClick={(event) => event.stopPropagation()}><ClassPanel item={selected} onClose={() => setSelected(null)} /></div></div>}
    </>
  );
}

function MapPage() {
  const [filter, setFilter] = useState("Best");
  return (
    <div className="map-page">
      <aside className="map-sidebar">
        <span className="eyebrow">Monday · Nov 2</span>
        <Heading>Find parking</Heading>
        <p>Near Olson Hall for your 10:00 am class.</p>
        <div className="date-chips">{["Today", "Mon", "Tue", "Wed", "Thu"].map((day, index) => <button className={index === 1 ? "active" : ""} key={day}>{day}</button>)}</div>
        <div className="filter-chips map-filters">{["Best", "Cheapest", "Closest"].map((item) => <button className={filter === item ? "active" : ""} onClick={() => setFilter(item)} key={item}>{item}</button>)}</div>
        <div className="ranked-lots">
          <div className="ranked-lot selected"><span className="rank">1</span><ZonePlate zone="L" large /><span><strong>Lot 2</strong><small>~10 min walk · 720 m</small></span><b>$3.75</b></div>
          <div className="ranked-lot"><span className="rank">2</span><ZonePlate zone="C" large /><span><strong>Lot 10</strong><small>~7 min walk · 510 m</small></span><b>$5.50</b></div>
          <div className="ranked-lot"><span className="rank">3</span><ZonePlate zone="C+" large /><span><strong>Lot 5</strong><small>~2 min walk · 160 m</small></span><b>$6.50</b></div>
        </div>
        <Button variant="secondary" icon="location" className="full-button">Use my location</Button>
      </aside>
      <div className="campus-map">
        <div className="map-road road-one" />
        <div className="map-road road-two" />
        <div className="map-road road-three" />
        <div className="map-green green-one" />
        <div className="map-green green-two" />
        <div className="building building-one">Olson Hall</div>
        <div className="building building-two">Hutchison</div>
        <div className="building building-three">Shields Library</div>
        <div className="lot-shape lot-one suggested"><ZonePlate zone="L" /><span>Lot 2</span></div>
        <div className="lot-shape lot-two"><ZonePlate zone="C+" /><span>Lot 5</span></div>
        <div className="lot-shape lot-three"><ZonePlate zone="C" /><span>Lot 10</span></div>
        <div className="route-line" />
        <div className="class-pin"><Icon name="location" size={26} /><span>10:00 · ECS 36A</span></div>
        <div className="map-legend"><strong>Student prices</strong><span><i className="scale l" /> L · $3.75</span><span><i className="scale c" /> C · $5.50</span><span><i className="scale cp" /> C+ · $6.50</span></div>
      </div>
    </div>
  );
}

function Toggle({ checked = true }: { checked?: boolean }) {
  const [on, setOn] = useState(checked);
  return <button className={`toggle ${on ? "on" : ""}`} role="switch" aria-checked={on} onClick={() => setOn(!on)}><span /></button>;
}

function SettingsPage() {
  const [saved, setSaved] = useState(false);
  const save = () => { setSaved(true); window.setTimeout(() => setSaved(false), 1800); };
  return (
    <>
      <div className="page-header"><div><span className="eyebrow">Make ParkOS yours</span><Heading>Settings</Heading><p>Changes save as you make them.</p></div></div>
      <div className="settings-layout" onClick={save}>
        <section className="settings-card">
          <div className="settings-heading"><span className="settings-icon"><Icon name="mail" /></span><div><Heading level={2}>Reminders</Heading><p>One email before your first class.</p></div></div>
          <div className="settings-row"><span><strong>Daily reminders</strong><small>Weekdays with an on-campus class</small></span><Toggle /></div>
          <div className="settings-row"><span><strong>Email</strong><small>Where your reminders go</small></span><span className="setting-value">student@ucdavis.edu <Icon name="chevron" /></span></div>
          <div className="settings-row"><span><strong>Lead time</strong><small>Before your first class</small></span><span className="setting-value">30 minutes <Icon name="chevron" /></span></div>
          <div className="settings-row"><span><strong>Walk limit</strong><small>For your Best parking option</small></span><span className="setting-value">10 minutes <Icon name="chevron" /></span></div>
        </section>
        <section className="settings-card">
          <div className="settings-heading"><span className="settings-icon"><Icon name="user" /></span><div><Heading level={2}>About you</Heading><p>Used to find the lots you're allowed to use.</p></div></div>
          <div className="settings-row"><span><strong>Affiliation</strong><small>Parking access and prices</small></span><span className="setting-value">Student <Icon name="chevron" /></span></div>
        </section>
        <section className="settings-card">
          <div className="settings-heading"><span className="settings-icon"><Icon name="calendar" /></span><div><Heading level={2}>Schedule</Heading><p>3 classes across 5 weekdays.</p></div></div>
          <div className="settings-buttons"><Button variant="secondary" icon="upload">Upload a new schedule</Button><Button variant="ghost">Clear everything</Button></div>
        </section>
      </div>
      {saved && <div className="toast"><Icon name="check" /> Saved</div>}
    </>
  );
}

export default function App() {
  const [screen, setScreen] = useState<Screen>("welcome");
  const [remindersOn, setRemindersOn] = useState(false);
  const onboardingBack: Record<string, Screen> = useMemo(() => ({
    role: "login",
    method: "role",
    upload: "method",
    grid: "method",
    buildings: "grid",
  }), []);

  if (screen === "welcome") return <Welcome onStart={() => setScreen("login")} />;
  if (screen === "login") return <Login onContinue={() => setScreen("role")} onBack={() => setScreen("welcome")} />;
  if (screen === "role") return <RoleStep next={() => setScreen("method")} back={() => setScreen("login")} />;
  if (screen === "method") return <MethodStep select={setScreen} back={() => setScreen("role")} />;
  if (screen === "upload") return <UploadStep back={() => setScreen("method")} review={() => setScreen("grid")} />;
  if (screen === "grid") return <GridStep next={() => setScreen("buildings")} back={() => setScreen(onboardingBack.grid)} />;
  if (screen === "buildings") return <BuildingsStep next={() => setScreen("week")} back={() => setScreen("grid")} />;

  return (
    <AppShell screen={screen} navigate={setScreen} remindersOn={remindersOn}>
      {screen === "week" && <WeekPage remindersOn={remindersOn} setRemindersOn={setRemindersOn} editReminders={() => setScreen("edit-reminders")} />}
      {screen === "edit-reminders" && <ReminderSettingsPage onDone={() => setScreen("week")} remindersOn={remindersOn} setRemindersOn={setRemindersOn} />}
      {screen === "schedule" && <SchedulePage />}
      {screen === "map" && <MapPage />}
      {screen === "settings" && <SettingsPage />}
    </AppShell>
  );
}
