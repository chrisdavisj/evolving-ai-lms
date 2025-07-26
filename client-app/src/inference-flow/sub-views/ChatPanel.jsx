import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
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
          {msg.role === "assistant" && msg.text.trim().startsWith("#") ? (
            <div className="chat-text">
              <ReactMarkdown components={{a: ({ node, ...props }) => {const href = props.href?.trim(); if (!href) {return <span>{props.children}</span>;}return (<a href={href} target="_blank" rel="noopener noreferrer">{props.children}</a>);},}}>
                {msg.text.replace(/^```(?:markdown)?\s*([\s\S]*?)```$/, "$1").trim()}
              </ReactMarkdown>
            </div>) : (<p className="chat-text">{msg.text}</p>)}
        </motion.div>
      ))}
    </div>
  );
}


