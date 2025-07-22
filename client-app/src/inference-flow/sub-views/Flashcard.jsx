import { X } from "lucide-react";
import "./Flashcard.css";

export default function Flashcard({ text, onDismiss }) {
  if (!text) return null;

  return (
    <div className="flashcard-card">
      <div className="flashcard-header">
        <p className="flashcard-text">{text}</p>
        <button onClick={onDismiss} className="flashcard-close">
          <X size={16} />
        </button>
      </div>
    </div>
  );
}
