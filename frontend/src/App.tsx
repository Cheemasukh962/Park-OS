import { ReactNode, useEffect, useMemo, useState } from "react";

import { OnboardingShell } from "./components/OnboardingShell";
import { getSettings, updateSettings } from "./api/client";
import type { Affiliation, ImportResult, Settings } from "./api/types";
import { Button, Field, Heading, Icon, type IconName, Logo, ZonePlate } from "./components/ui";
import { type DraftClass, toDraft } from "./lib/schedule";
import { BuildingsStep } from "./screens/onboarding/BuildingsStep";
import { GridStep } from "./screens/onboarding/GridStep";
import { UploadStep } from "./screens/onboarding/UploadStep";
import { MapPage } from "./screens/MapPage";
import { ReminderSettingsPage } from "./screens/ReminderSettingsPage";
import { SchedulePage } from "./screens/SchedulePage";
import { SettingsPage } from "./screens/SettingsPage";
import { WeekPage } from "./screens/WeekPage";

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

function RoleStep({ choose, back }: { choose: (affiliation: Affiliation) => void; back: () => void }) {
  // Students only for now. Staff and visitors work in the back end (zone_rates.csv), but their
  // screens aren't finished, so that card is shown as coming soon and can't be picked.
  return (
    <OnboardingShell step={1} onBack={back}>
      <div className="step-heading">
        <span className="eyebrow">First, a quick question</span>
        <Heading>Who are you?</Heading>
        <p>Parking access changes by affiliation. ParkOS is for students right now.</p>
      </div>
      <div className="choice-grid role-grid" role="radiogroup" aria-label="Affiliation">
        <button className="choice-card" role="radio" aria-checked="false" onClick={() => choose("student")}>
          <span className="choice-icon"><Icon name="user" size={24} /></span>
          <span>
            <strong>Student</strong>
            <small>Cheapest lots for you. A zone after 5 pm only.</small>
          </span>
          <Icon name="chevron" />
        </button>
        <div className="choice-card disabled" role="radio" aria-checked="false" aria-disabled="true">
          <span className="choice-icon"><Icon name="calendar" size={24} /></span>
          <span>
            <strong>Staff, faculty or visitor</strong>
            <small>Coming soon. Different zones and prices apply, and we're still building that.</small>
          </span>
          <span className="soon-badge">Soon</span>
        </div>
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
            <small>Calendar file (.ics) or Schedule Builder PDF</small>
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

const AFFILIATION_LABELS: Record<Affiliation, string> = { student: "Student", staff: "Staff", visitor: "Visitor" };

const navItems: { screen: Screen; label: string; icon: IconName }[] = [
  { screen: "week", label: "This week", icon: "calendar" },
  { screen: "schedule", label: "Schedule", icon: "grid" },
  { screen: "map", label: "Map", icon: "map" },
  { screen: "settings", label: "Settings", icon: "gear" },
];

function AppShell({
  screen,
  navigate,
  settings,
  children,
}: {
  screen: Screen;
  navigate: (screen: Screen) => void;
  settings: Settings | null;
  children: ReactNode;
}) {
  const remindersOn = settings?.reminders_enabled ?? false;
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
          <span className={`status-dot ${remindersOn ? "" : "off"}`}><i /> Reminders {remindersOn ? `on · ${settings?.lead_minutes} min` : "off"}</span>
          <span className="affiliation"><Icon name="user" size={16} /> {AFFILIATION_LABELS[settings?.affiliation ?? "student"]}</span>
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

export default function App() {
  const [screen, setScreen] = useState<Screen>("welcome");
  const [settings, setSettings] = useState<Settings | null>(null);
  // Classes being set up during onboarding: filled by an upload or by hand, saved at the last step
  const [drafts, setDrafts] = useState<DraftClass[]>([]);
  const [imported, setImported] = useState<ImportResult | null>(null);
  const onboardingBack: Record<string, Screen> = useMemo(() => ({
    role: "login",
    method: "role",
    upload: "method",
    grid: imported ? "upload" : "method",
    buildings: "grid",
  }), [imported]);

  // Settings come from the API; every change is saved there and the returned copy kept here
  useEffect(() => {
    getSettings().then(setSettings).catch(() => setSettings(null));
  }, []);
  const saveSettings = async (changes: Partial<Settings>) => setSettings(await updateSettings(changes));

  const showImported = (result: ImportResult) => {
    setImported(result);
    setDrafts(result.classes.map((item) => toDraft(item)));
    setScreen("grid");
  };
  const fillInMyself = () => {
    setImported(null);
    setDrafts([]);
    setScreen("grid");
  };

  if (screen === "welcome") return <Welcome onStart={() => setScreen("login")} />;
  if (screen === "login") return <Login onContinue={() => setScreen("role")} onBack={() => setScreen("welcome")} />;
  if (screen === "role") return <RoleStep choose={(affiliation) => { saveSettings({ affiliation }).catch(() => {}); setScreen("method"); }} back={() => setScreen("login")} />;
  if (screen === "method") return <MethodStep select={(next) => (next === "grid" ? fillInMyself() : setScreen(next))} back={() => setScreen("role")} />;
  if (screen === "upload") return <UploadStep back={() => setScreen("method")} fillInMyself={fillInMyself} onImported={showImported} />;
  if (screen === "grid") return <GridStep classes={drafts} setClasses={setDrafts} imported={imported} next={() => setScreen("buildings")} back={() => setScreen(onboardingBack.grid)} />;
  if (screen === "buildings") return <BuildingsStep classes={drafts} setClasses={setDrafts} next={() => setScreen("week")} back={() => setScreen("grid")} />;

  return (
    <AppShell screen={screen} navigate={setScreen} settings={settings}>
      {!settings && <p className="form-error" role="alert">Can't reach the ParkOS server. Is it running on port 5000?</p>}
      {screen === "week" && settings && (
        <WeekPage settings={settings} saveSettings={saveSettings} editReminders={() => setScreen("edit-reminders")} />
      )}
      {screen === "edit-reminders" && settings && (
        <ReminderSettingsPage settings={settings} saveSettings={saveSettings} onDone={() => setScreen("week")} />
      )}
      {screen === "schedule" && <SchedulePage uploadSchedule={() => setScreen("upload")} />}
      {screen === "map" && <MapPage defaultPriority={settings?.priority ?? "best"} />}
      {screen === "settings" && settings && (
        <SettingsPage settings={settings} saveSettings={saveSettings}
                      editEmail={() => setScreen("edit-reminders")} uploadSchedule={() => setScreen("upload")} />
      )}
    </AppShell>
  );
}
