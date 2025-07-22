import { motion } from "framer-motion";
import "./ChatPanel.css";

export default function ChatPanel({ chatHistory }) {
  return (
    <div className="chat-panel">
      {chatHistory.map((msg, idx) => (
        <motion.div
          key={idx}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className={`chat-bubble ${msg.role}`}
        >
          {msg.image && <img src={msg.image} alt="" className="chat-image" />}
          <p className="chat-text">{msg.text}</p>
        </motion.div>
      ))}
    </div>
  );
}


