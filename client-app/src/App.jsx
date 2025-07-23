import React, { useState } from "react";
import InferenceWindow from './inference-flow/InferenceWindow';
import OnboardingWindow from "./onboarding-flow/OnboardingWindow";
import { Button } from "./reusable-ui-components/Button";
import "./App.css";
import "./Landing.css";

function App() {
  const [view, setView] = useState("landing");
  const [completedOnboarding, setCompletedOnboarding] = useState(
    !!localStorage.getItem("onboardingData")
  );

  const handleOnboardingComplete = () => {
    setCompletedOnboarding(true);
    setView("landing");
  };

  if (view === "onboarding-start") {
    return (
      <OnboardingWindow
        onComplete={handleOnboardingComplete}
        onBack={() => setView("landing")}
      />
    );
  }

  if (view === "inference") {
    return (
      <main className="inference-screen">
        <div className="nav-header">
          <Button onClick={() => setView("landing")}>←</Button>
        </div>
        <InferenceWindow />
      </main>
    );
  }

  return (
    <main className="landing-container">
      <div className="landing-card">
        <h1 className="landing-title">Welcome to Evolving AI LMS</h1>
        <div className="landing-buttons">
          {!completedOnboarding ? (
            <Button onClick={() => setView("onboarding-start")}>Start Onboarding</Button>
          ) : (
            <>
              <Button onClick={() => setView("onboarding-start")}>Onboarding</Button>
              <Button onClick={() => setView("inference")}>Inference</Button>
            </>
          )}
        </div>
      </div>
    </main>
  );
}

export default App;
