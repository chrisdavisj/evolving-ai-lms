import { Button } from "../../reusable-ui-components/Button";
import "./CameraPanel.css"; 
import Flashcard from "./Flashcard";

export default function CameraPanel({
  capturedImage,
  videoRef,
  canvasRef,
  startCamera,
  captureImage,
  setCapturedImage,
  flashcard,
  dismissFlashcard
}) {
  return (
    <div className="media-viewer">
      <div className="media-wrapper">
        {!capturedImage ? (
          <>
            <video ref={videoRef} autoPlay className="media-display" />
            <Button onClick={startCamera} className="mt-2">Start Camera</Button>
            <Button onClick={captureImage} className="mt-2">Capture</Button>
          </>
        ) : (
          <>
            <img src={capturedImage} alt="Captured" className="media-display" />
            <Button onClick={() => setCapturedImage(null)} className="mt-2">Recapture</Button>
          </>
        )}
        <canvas ref={canvasRef} style={{ display: 'none' }} />
        {flashcard && (
          <div className="flashcard-overlay">
            <Flashcard text={flashcard} onDismiss={dismissFlashcard} />
          </div>
        )}
      </div>
    </div>
  );
}
