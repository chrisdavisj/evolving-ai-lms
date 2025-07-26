import { X } from "lucide-react";
import "./Flashcard.css";
import ReactMarkdown from "react-markdown";

export default function Flashcard({ text, onDismiss }) {
  if (!text) return null;

  const cleanedText = cleanMarkdown(text);
  return (
    <div className="flashcard-card">
      <div className="flashcard-header">
        <div className="flashcard-text">
          <ReactMarkdown>{cleanedText}</ReactMarkdown>
        </div>
        <button onClick={onDismiss} className="flashcard-close">
          <X size={12} />
        </button>
      </div>
    </div>
  );
}

function cleanMarkdown(text) {
  return text.replace(/^```(?:\w+)?\s*([\s\S]*?)```$/, "$1").trim();
}