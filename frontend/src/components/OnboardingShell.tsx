// The frame around each onboarding step: logo, "Step 2 of 4" bars, and a Back button.
import type { ReactNode } from "react";

import { Button, Logo } from "./ui";

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

export function OnboardingShell({
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
