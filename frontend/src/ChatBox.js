import React, { useState } from "react";

const SESSION_ID = "resume-chat-1";

export default function ChatBox() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);

  const sendMessage = async (e) => {
    e.preventDefault();
    const query = input.trim();
    if (!query) return;

    setMessages((prev) => [...prev, { role: "user", content: query }]);
    setInput("");

    try {
      const res = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: query,
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Chat error");
      }

      const data = await res.json();

      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.answer },
      ]);
    } catch (err) {
      alert(err.message);
    }
  };

  return (
    <div className="inline-chat-container">
      <h2 className="inline-chat-title">Career Coach Chatbot</h2>

      <div className="inline-chat-box">
        {messages.map((m, idx) => (
          <div
            key={idx}
            className={`chat-row ${m.role === "user" ? "right" : "left"}`}
          >
            <div
              className={`chat-bubble ${
                m.role === "user" ? "user-bubble" : "assistant-bubble"
              }`}
            >
              {m.content}
            </div>
          </div>
        ))}

        {messages.length === 0 && (
          <div className="chat-empty">
            <p>Ask anything about your resume or JD to get AI guidance.</p>
          </div>
        )}
      </div>

      <form onSubmit={sendMessage} className="chat-input-form">
        <input
          type="text"
          placeholder="Ask about your resume or JD..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          className="chat-input"
        />
        <button type="submit" className="chat-send-btn">
          Send
        </button>
      </form>
    </div>
  );
}
