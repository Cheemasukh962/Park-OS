// Onboarding step 2: upload a schedule file, and the API reads the classes out of it.
import { type ChangeEvent, useState } from "react";

import { ApiRequestError, importSchedule } from "../../api/client";
import type { ImportResult } from "../../api/types";
import { OnboardingShell } from "../../components/OnboardingShell";
import { Button, Heading, Icon } from "../../components/ui";

type Props = {
  back: () => void;
  fillInMyself: () => void;
  onImported: (result: ImportResult) => void;
};

export function UploadStep({ back, fillInMyself, onImported }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [reading, setReading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const chooseFile = (event: ChangeEvent<HTMLInputElement>) => {
    setFile(event.target.files?.[0] ?? null);
    setError(null);
  };

  const read = async () => {
    if (!file) return;
    setReading(true);
    setError(null);
    try {
      onImported(await importSchedule(file));                  // the parent shows the classes on the grid
    } catch (problem) {
      setError(problem instanceof ApiRequestError ? problem.message : "Something went wrong reading that file.");
    } finally {
      setReading(false);
    }
  };

  return (
    <OnboardingShell step={2} onBack={back}>
      <div className="step-heading">
        <span className="eyebrow">Schedule import</span>
        <Heading>Upload your schedule</Heading>
        <p>We'll read your classes and put them on the grid for you to check.</p>
      </div>
      <label className={`drop-zone ${file ? "has-file" : ""}`}>
        <input type="file" accept=".ics,.pdf,text/calendar,application/pdf" onChange={chooseFile} />
        <span className="drop-icon"><Icon name={file ? "check" : "upload"} size={28} /></span>
        <strong>{file?.name || "Drop your schedule here"}</strong>
        <small>
          {file ? "Ready to read your schedule"
                : "Calendar file (.ics, best) or Schedule Builder PDF · up to 5 MB"}
        </small>
        <span className="button button-secondary">{file ? "Choose a different file" : "Choose file"}</span>
      </label>
      <p className="privacy-note">
        Tip: in Schedule Builder, export to calendar for an exact .ics file. Printing the page to PDF works too.
      </p>
      {error && <p className="form-error upload-error" role="alert">{error}</p>}
      <div className="upload-footer">
        <Button variant="ghost" onClick={fillInMyself}>Fill it in myself</Button>
        <Button onClick={read} disabled={!file || reading}>{reading ? "Reading…" : "Read my schedule"}</Button>
      </div>
    </OnboardingShell>
  );
}
