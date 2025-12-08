import React, { useState } from "react";

const SESSION_ID = "resume-chat-1";

export default function ChatDrawer() {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);

  const toggleDrawer = () => setOpen(!open);

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
          message: query, // MUST BE EXACT NAME
        }),
      });

      const data = await res.json();

      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.answer },
      ]);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <>
      {/* Floating Chat Button */}
      <button
        onClick={toggleDrawer}
        className="chat-fab"
        aria-label="Open career coach chat"
      >
        💬
      </button>

      {/* Dimmed background */}
      <div
        className={`chat-backdrop ${open ? "open" : ""}`}
        onClick={toggleDrawer}
      />

      {/* Sliding drawer */}
      <aside className={`chat-drawer ${open ? "open" : ""}`}>
        <header className="chat-drawer-header">
          <div>
            <h2>Career Coach</h2>
            <p>Ask anything about your resume, JD or skills.</p>
          </div>
          <button
            onClick={toggleDrawer}
            className="chat-close-btn"
            aria-label="Close chat"
          >
            ✕
          </button>
        </header>

        <div className="chat-messages">
          {messages.map((m, i) => (
            <div
              key={i}
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
              <p>Try asking:</p>
              <ul>
                <li>“How can I improve this resume for frontend roles?”</li>
                <li>“Which skills should I learn first from the missing list?”</li>
              </ul>
            </div>
          )}
        </div>

        <form onSubmit={sendMessage} className="chat-input-form">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask your career coach..."
            className="chat-input"
          />
          <button type="submit" className="chat-send-btn">
            ➤
          </button>
        </form>
      </aside>
    </>
  );
}
