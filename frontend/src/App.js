import React, { useState } from "react";
import ChatDrawer from "./ChatDrawer";

function App() {
  const [resumeFile, setResumeFile] = useState(null);
  const [resumeText, setResumeText] = useState("");
  const [jdFile, setJdFile] = useState(null);
  const [jdText, setJdText] = useState("");
  const [result, setResult] = useState("");
  const [parsed, setParsed] = useState(null);
  const [loading, setLoading] = useState(false);

  const analyze = async () => {
    setLoading(true);
    setResult("");
    setParsed(null);

    const formData = new FormData();

    if (resumeFile) formData.append("resume_file", resumeFile);
    else if (resumeText.trim() !== "") formData.append("resume_text", resumeText);

    if (jdFile) formData.append("jd_file", jdFile);
    else if (jdText.trim() !== "") formData.append("jd_text", jdText);

    try {
      const res = await fetch("http://localhost:8000/analyze", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error("Backend error");

      const data = await res.json();
      setResult(JSON.stringify(data, null, 2));
      setParsed(data);
    } catch (error) {
      alert("❌ Backend not running.");
    }

    setLoading(false);
  };

  const cardStyle = {
    background: "#fff7d1",
    padding: "25px",
    borderRadius: "12px",
    marginBottom: "25px",
    boxShadow: "0 0 15px rgba(0,0,0,0.1)",
  };

  const containerStyle = {
    width: "70%",
    margin: "auto",
    padding: "30px",
    fontFamily: "Arial, sans-serif",
  };

  return (
    <div style={containerStyle}>
      <h1 style={{ textAlign: "center", marginBottom: "30px" }}>
        🚀 Career Compass – Resume/JD Analyzer
      </h1>

      {/* UPLOAD FORM */}
      <form>
        <div style={cardStyle}>
          <h2>Upload Resume (PDF) or Paste Text</h2>
          <input
            type="file"
            onChange={(e) => {
              setResumeFile(e.target.files[0]);
              setResumeText("");
            }}
          />
          <textarea
            placeholder="Or paste resume text..."
            value={resumeText}
            onChange={(e) => {
              setResumeText(e.target.value);
              setResumeFile(null);
            }}
            style={{ width: "100%", height: "120px", marginTop: "10px" }}
          />
        </div>

        <div style={cardStyle}>
          <h2>Upload Job Description or Paste Text</h2>
          <input
            type="file"
            onChange={(e) => {
              setJdFile(e.target.files[0]);
              setJdText("");
            }}
          />
          <textarea
            placeholder="Or paste JD text..."
            value={jdText}
            onChange={(e) => {
              setJdText(e.target.value);
              setJdFile(null);
            }}
            style={{ width: "100%", height: "120px", marginTop: "10px" }}
          />
        </div>

        <div style={{ textAlign: "center" }}>
          <button
            type="button"
            onClick={analyze}
            style={{
              padding: "12px 25px",
              background: "#ffcc00",
              borderRadius: "10px",
              border: "none",
              fontSize: "18px",
              cursor: "pointer",
              fontWeight: "bold",
            }}
          >
            {loading ? "Analyzing..." : "Analyze"}
          </button>
        </div>
      </form>

      {/* BEAUTIFUL ANALYSIS UI */}
      {parsed && (
        <div
          style={{
            marginTop: "40px",
            background: "#fffbea",
            padding: "30px",
            borderRadius: "15px",
            boxShadow: "0 4px 15px rgba(0,0,0,0.1)",
          }}
        >
          <h2>📊 Analysis Results</h2>

          {/* SCORES */}
          <div style={{ display: "flex", gap: "40px", marginBottom: "30px" }}>
            <div style={{ textAlign: "center" }}>
              <div
                style={{
                  width: "130px",
                  height: "130px",
                  background: "#ffe066",
                  borderRadius: "50%",
                  display: "flex",
                  justifyContent: "center",
                  alignItems: "center",
                  fontSize: "28px",
                  fontWeight: "bold",
                }}
              >
                {parsed.similarity_score?.toFixed(2)}
              </div>
              <p>Similarity Score</p>
            </div>

            <div style={{ textAlign: "center" }}>
              <div
                style={{
                  width: "130px",
                  height: "130px",
                  background: "#ffd43b",
                  borderRadius: "50%",
                  display: "flex",
                  justifyContent: "center",
                  alignItems: "center",
                  fontSize: "28px",
                  fontWeight: "bold",
                }}
              >
                {parsed.match_score_0_10}
              </div>
              <p>Match Score (0–10)</p>
            </div>
          </div>

          {/* SKILLS */}
          <h3>Matched Skills ✅</h3>
          <div>
            {parsed.skills?.matched_skills?.map((s, i) => (
              <span
                key={i}
                style={{
                  background: "#d3f9d8",
                  padding: "8px 14px",
                  borderRadius: "20px",
                  marginRight: "8px",
                  marginBottom: "8px",
                  display: "inline-block",
                }}
              >
                {s}
              </span>
            ))}
          </div>

          <h3 style={{ marginTop: "20px" }}>Missing Skills ❌</h3>
          <div>
            {parsed.skills?.missing_skills?.map((s, i) => (
              <span
                key={i}
                style={{
                  background: "#ffc9c9",
                  padding: "8px 14px",
                  borderRadius: "20px",
                  marginRight: "8px",
                  marginBottom: "8px",
                  display: "inline-block",
                }}
              >
                {s}
              </span>
            ))}
          </div>

          <h3 style={{ marginTop: "20px" }}>Extra Skills 📌</h3>
          <div>
            {parsed.skills?.extra_skills?.map((s, i) => (
              <span
                key={i}
                style={{
                  background: "#cce5ff",
                  padding: "8px 14px",
                  borderRadius: "20px",
                  marginRight: "8px",
                  marginBottom: "8px",
                  display: "inline-block",
                }}
              >
                {s}
              </span>
            ))}
          </div>

          {/* AI SUMMARY SECTION FIXED */}
          <h3 style={{ marginTop: "30px" }}>🧠 AI Summary</h3>
          <p style={{ whiteSpace: "pre-wrap", fontSize: "18px" }}>
            {parsed.llm_analysis || "No analysis provided."}
          </p>

          {/* OLD JSON-BASED SECTIONS (COMMENTED OUT) */}
          {/*
          <h3 style={{ marginTop: "20px" }}>💪 Technical Strengths</h3>
          <ul>
            {parsed.llm_analysis?.technical_strengths?.map((t, i) => (
              <li key={i}>{t}</li>
            ))}
          </ul>

          <h3 style={{ marginTop: "20px" }}>⚠️ Missing Skills Impact</h3>
          ... (OLD UI HIDDEN)
          */}
        </div>
      )}

      {/* RAW JSON (optional debug) */}
      {result && (
        <pre
          style={{
            background: "#f3f3f3",
            padding: "20px",
            borderRadius: "10px",
            marginTop: "25px",
            maxHeight: "500px",
            overflow: "auto",
          }}
        >
          {result}
        </pre>
      )}

      {/* CHAT DRAWER */}
      <ChatDrawer />
    </div>
  );
}

export default App;
