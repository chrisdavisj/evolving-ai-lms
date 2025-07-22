import { UploadCloud } from "lucide-react";
import Flashcard from "./Flashcard";
import "./ImageUploader.css";
import "./Flashcard.css";

export default function ImageUploader({
  image,
  handleImageUpload,
  flashcard,
  dismissFlashcard,
}) {

  return (
    <div className="media-viewer">
      <div className="media-wrapper">
        <label htmlFor="file-upload" className="custom-upload-button">
          <UploadCloud className="icon" />
          Choose an Image
        </label>
        <input
          id="file-upload"
          type="file"
          accept="image/*"
          onChange={handleImageUpload}
          className="hidden-file-input"
        />
        {image && (
          <div className="image-preview-wrapper">
            <img src={image} alt="Uploaded" className="media-display" />
            {flashcard && (
              <div className="flashcard-overlay">
                <Flashcard text={flashcard} onDismiss={dismissFlashcard} />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
