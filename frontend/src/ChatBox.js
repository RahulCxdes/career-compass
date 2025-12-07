// ChatBox.jsx
import React, { useState } from "react";

const SESSION_ID = "resume-chat-1"; // could be random per tab / user

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
        message: query,   // FIXED!
      }),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Chat error");
    }

    const data = await res.json();

    setMessages((prev) => [
      ...prev,
      {
        role: "assistant",
        content: data.answer,
      },
    ]);
  } catch (err) {
    alert(err.message);
  }
};


  return (
    <div className="chat-container" style={{ marginTop: "40px" }}>
      <h2>💬 Career Coach Chatbot</h2>

      <div
        className="chat-messages"
        style={{
          background: "white",
          height: "250px",
          overflowY: "auto",
          padding: "10px",
          borderRadius: "10px",
          marginBottom: "15px",
          border: "1px solid #ccc",
        }}
      >
        {messages.map((m, idx) => (
          <div
            key={idx}
            style={{
              marginBottom: "12px",
              textAlign: m.role === "user" ? "right" : "left",
            }}
          >
            <strong>{m.role === "user" ? "You" : "Coach"}:</strong>
            <p>{m.content}</p>
          </div>
        ))}
      </div>

      <form onSubmit={sendMessage} className="chat-input-row">
        <input
          type="text"
          placeholder="Ask about your resume or JD..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          style={{
            width: "75%",
            padding: "10px",
            borderRadius: "8px",
            border: "1px solid #aaa",
          }}
        />
        <button
          type="submit"
          style={{
            padding: "10px 15px",
            background: "#ffcc00",
            border: "none",
            borderRadius: "8px",
            marginLeft: "10px",
            fontWeight: "bold",
            cursor: "pointer",
          }}
        >
          Send
        </button>
      </form>
    </div>
  );
}
