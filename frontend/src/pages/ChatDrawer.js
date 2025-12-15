import React, { useState, useEffect } from "react";
import "../styles/ChatDrawer.css";

export default function ChatDrawer() {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [recordingStatus, setRecordingStatus] = useState("");

  useEffect(() => {
    window.speechSynthesis.onvoiceschanged = () => {};
  }, []);

  const speak = (text) => {
    if (!text || !window.speechSynthesis || !voiceEnabled) return;

    window.speechSynthesis.cancel();
    const utter = new SpeechSynthesisUtterance(text);
    utter.rate = 1;
    window.speechSynthesis.speak(utter);
  };

  let mediaRecorder;
  let audioChunks = [];

  const startVoiceInput = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      mediaRecorder = new MediaRecorder(stream);
      audioChunks = [];
      mediaRecorder.start();

      setRecordingStatus("🎙️ Listening...");

      mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);

      mediaRecorder.onstop = async () => {
        setRecordingStatus("⏳ Processing...");

        const audioBlob = new Blob(audioChunks, { type: "audio/wav" });
        const formData = new FormData();
        formData.append("audio", audioBlob, "recording.wav");

        const res = await fetch("http://localhost:8000/api/speech-to-text", {
          method: "POST",
          body: formData,
        });

        const data = await res.json();
        setInput(data.text);

        setRecordingStatus(""); 
      };

      setTimeout(() => mediaRecorder.stop(), 4000);
    } catch (e) {
    
      setRecordingStatus("⚠️ Microphone blocked");
      setTimeout(() => setRecordingStatus(""), 2000);
    }
  };


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
        body: JSON.stringify({ message: query }),
      });

      const data = await res.json();

      setMessages((prev) => [...prev, { role: "assistant", content: data.answer }]);

      if (voiceEnabled) speak(data.answer);

    } catch (e) {
      setRecordingStatus("⚠️ Chat error");
      setTimeout(() => setRecordingStatus(""), 2000);
    }
  };

  return (
    <>
      <button onClick={() => setOpen(true)} className="chat-fab">💬</button>

      <div className={`chat-backdrop ${open ? "open" : ""}`} onClick={() => setOpen(false)} />

      <aside className={`chat-drawer ${open ? "open" : ""}`}>
        <header className="chat-drawer-header">
          <h2>Career Coach</h2>
          <button onClick={() => setOpen(false)} className="chat-close-btn">✕</button>
        </header>


        {recordingStatus && (
          <div className="recording-status">{recordingStatus}</div>
        )}

        <div className="chat-messages">
          {messages.map((m, i) => (
            <div key={i} className={`chat-row ${m.role === "user" ? "right" : "left"}`}>
              <div className={`chat-bubble ${m.role === "user" ? "user-bubble" : "assistant-bubble"}`}>
                {m.content}
              </div>
            </div>
          ))}
        </div>

        <form onSubmit={sendMessage} className="chat-input-form">
          <input
            className="chat-input"
            placeholder="Ask career coach..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />

          <button type="button" className="chat-mic-btn" onClick={startVoiceInput}>
            🎤
          </button>

          <button
            type="button"
            className="chat-voice-toggle"
            onClick={() => {
              window.speechSynthesis.cancel();
              setVoiceEnabled(!voiceEnabled);
            }}
          >
            {voiceEnabled ? "🔊" : "🔈"}
          </button>

          <button type="submit" className="chat-send-btn">➤</button>
        </form>
      </aside>
    </>
  );
}
