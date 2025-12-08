import React, { useState } from "react";

export default function Analyzer() {
  const [resumeFile, setResumeFile] = useState(null);
  const [resumeText, setResumeText] = useState("");
  const [jdFile, setJdFile] = useState(null);
  const [jdText, setJdText] = useState("");
  const [parsed, setParsed] = useState(null);
  const [loading, setLoading] = useState(false);

  

  const analyze = async () => {
    setLoading(true);
    setParsed(null);

    const formData = new FormData();

    if (resumeFile) formData.append("resume_file", resumeFile);
    else if (resumeText.trim()) formData.append("resume_text", resumeText);

    if (jdFile) formData.append("jd_file", jdFile);
    else if (jdText.trim()) formData.append("jd_text", jdText);

    try {
      const res = await fetch("http://localhost:8000/analyze", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      setParsed(data);
    } catch {
      alert("Error reaching backend");
    }

    setLoading(false);
  };

  return (
    <div className="analyzer-container">
      <h2 className="page-title">Resume & Job Description Analyzer</h2>

      <div className="glass-panel analyzer-panel">

        <div className="upload-grid">

          {/* Resume */}
          <div className="glass-card">
            <h3>Resume</h3>

            <label className="file-input-label">
              <span>{resumeFile ? resumeFile.name : "Upload Resume PDF"}</span>
              <input
                type="file"
                onChange={(e) => {
                  setResumeFile(e.target.files[0]);
                  setResumeText("");
                }}
              />
            </label>

            <div className="divider-label"><span>or paste text</span></div>

            <textarea
              className="textarea"
              placeholder="Paste resume text..."
              value={resumeText}
              onChange={(e) => {
                setResumeText(e.target.value);
                setResumeFile(null);
              }}
            />
          </div>

          {/* JD */}
          <div className="glass-card">
            <h3>Job Description</h3>

            <label className="file-input-label">
              <span>{jdFile ? jdFile.name : "Upload JD file"}</span>
              <input
                type="file"
                onChange={(e) => {
                  setJdFile(e.target.files[0]);
                  setJdText("");
                }}
              />
            </label>

            <div className="divider-label"><span>or paste text</span></div>

            <textarea
              className="textarea"
              placeholder="Paste JD text..."
              value={jdText}
              onChange={(e) => {
                setJdText(e.target.value);
                setJdFile(null);
              }}
            />
          </div>

        </div>

        <div className="action-bar">
          <button
            onClick={analyze}
            className={`primary-btn ${loading ? "is-loading" : ""}`}
          >
            {loading ? "Analyzing..." : "Analyze"}
          </button>
        </div>
      </div>

      {/* RESULTS */}
      {parsed && (
        <div className="results-section">
          <h3>Results</h3>

          <div className="score-grid">
            <div className="score-card">
              <div className="score-circle">
                {parsed.similarity_score?.toFixed(2)}
              </div>
              <p>Similarity</p>
            </div>

            <div className="score-card">
              <div className="score-circle secondary">
                {parsed.match_score_0_10}
              </div>
              <p>Match Score</p>
            </div>
          </div>

          <h4>Matched Skills</h4>
          {parsed.skills?.matched_skills?.map((s, i) => (
            <span className="skill-badge badge-match" key={i}>{s}</span>
          ))}

          <h4>Missing Skills</h4>
          {parsed.skills?.missing_skills?.map((s, i) => (
            <span className="skill-badge badge-missing" key={i}>{s}</span>
          ))}

          <h4>Extra Skills</h4>
          {parsed.skills?.extra_skills?.map((s, i) => (
            <span className="skill-badge badge-extra" key={i}>{s}</span>
          ))}

          <div className="summary-card">
        <h4 className="summary-title">AI Summary</h4>
        <p className="summary-text">{parsed.llm_analysis}</p>
      </div>

        </div>
      )}
    </div>
  );
}
