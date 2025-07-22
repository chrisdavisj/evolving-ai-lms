import { Button } from "../../reusable-ui-components/Button";
import { Mic, Send, LoaderCircle, StopCircle } from "lucide-react";
import "./ControlsPanel.css";

const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);

export default function ControlsPanel({
  text,
  listening,
  transcribing,
  startRecording,
  stopRecording,
  handleSubmit
}) {
  
  return (
    <>
      <div className="controls">
        {listening ? (
          <Button onClick={stopRecording} variant="destructive">
            <StopCircle className="icon" />
            Stop Recording
          </Button>
        ) : (
          <Button onClick={startRecording} disabled={transcribing}>
            {transcribing ? <LoaderCircle className="icon spin" /> : <Mic className="icon" />}
            {transcribing ? "Transcribing..." : "Start Recording"}
          </Button>
        )}
        <span className="transcription-text">{text}</span>
      </div>
      <Button
        onClick={handleSubmit}
        disabled={!text}
        className="submit-button"
      >
        <Send className="icon" /> Send
      </Button>
    </>
  );
}
