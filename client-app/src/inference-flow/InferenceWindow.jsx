import React, { useState } from "react";
import { Camera, ImageIcon } from "lucide-react";
import { Button } from "../reusable-ui-components/Button"

import "./InferenceWindow.css";

export default function InferenceWindow() {
  const [mode, setMode] = useState(null);

  return (
    <div className="app-container">
      <div className="app-content">
        <div className="main-panel">
          <h1 className="heading">Evolving AI LMS</h1>
          {!mode && (
            <div className="mode-selector">
              <Button onClick={() => setMode('camera')}><Camera className="icon" /> Use Camera</Button>
              <Button onClick={() => setMode('image')}><ImageIcon className="icon" /> Upload Image</Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}


