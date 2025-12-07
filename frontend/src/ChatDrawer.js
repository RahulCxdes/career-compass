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
        message: query,   // MUST BE EXACT NAME
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
      {/* Floating Button */}
      <button
        onClick={toggleDrawer}
        style={{
          position: "fixed",
          bottom: "25px",
          right: "25px",
          background: "#ffcc00",
          border: "none",
          borderRadius: "50%",
          width: "60px",
          height: "60px",
          fontSize: "24px",
          cursor: "pointer",
          boxShadow: "0 4px 10px rgba(0,0,0,0.3)",
        }}
      >
        💬
      </button>

      {/* Slide Drawer */}
      <div
        style={{
          position: "fixed",
          top: "0",
          right: open ? "0" : "-400px",
          width: "350px",
          height: "100%",
          background: "#fffbe6",
          boxShadow: "-4px 0 10px rgba(0,0,0,0.2)",
          transition: "right 0.3s ease-in-out",
          padding: "20px",
          zIndex: 999,
        }}
      >
        <h2 style={{ marginBottom: "10px" }}>Career Coach</h2>

        {/* Messages */}
        <div
          style={{
            height: "75%",
            overflowY: "auto",
            marginBottom: "15px",
            padding: "10px",
            background: "#ffffff",
            borderRadius: "10px",
            border: "1px solid #ddd",
          }}
        >
          {messages.map((m, i) => (
            <div
              key={i}
              style={{
                textAlign: m.role === "user" ? "right" : "left",
                marginBottom: "12px",
              }}
            >
              <span
                style={{
                  display: "inline-block",
                  padding: "10px",
                  borderRadius: "10px",
                  background: m.role === "user" ? "#ffe066" : "#fff3cd",
                  maxWidth: "85%",
                }}
              >
                {m.content}
              </span>
            </div>
          ))}
        </div>

        {/* Input */}
        <form onSubmit={sendMessage} style={{ display: "flex" }}>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask anything..."
            style={{
              flex: 1,
              padding: "10px",
              border: "1px solid #ccc",
              borderRadius: "10px",
              marginRight: "10px",
            }}
          />
          <button
            type="submit"
            style={{
              padding: "10px 15px",
              background: "#ffcc00",
              border: "none",
              borderRadius: "10px",
              cursor: "pointer",
              fontWeight: "bold",
            }}
          >
            ➤
          </button>
        </form>
      </div>
    </>
  );
}
