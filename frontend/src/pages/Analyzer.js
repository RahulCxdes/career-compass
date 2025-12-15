import React, { useState } from "react";
import { marked } from "marked";
import "./Analyzer.css";


function formatSummary(text) {
  return { __html: marked.parse(text) };
}


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

{parsed && (
  <div className="results-section">

    <h3 className="results-title">Analysis Results</h3>

    <div className="score-wrapper">
      <div 
        className={`score-meter ${
          parsed.match_score_0_10 >= 8
            ? "high"
            : parsed.match_score_0_10 >= 5
            ? "medium"
            : "low"
        }`}
        style={{ "--percent": parsed.match_score_0_10 * 10 }}
      >
        <div className="score-meter-inner">
          {parsed.match_score_0_10}
          <span className="score-label-text">
            {parsed.match_score_0_10 >= 8
              ? "High Match"
              : parsed.match_score_0_10 >= 5
              ? "Medium Match"
              : "Low Match"}
          </span>
        </div>
      </div>
    </div>

    <div className="skills-wrapper">
      <h4>Matched Skills</h4>
      <div className="skills-badges">
        {parsed.skills?.matched_skills?.map((s, i) => (
          <span className="skill-badge badge-match" key={i}>{s}</span>
        ))}
      </div>

      <h4>Missing Skills</h4>
      <div className="skills-badges">
        {parsed.skills?.missing_skills?.map((s, i) => (
          <span className="skill-badge badge-missing" key={i}>{s}</span>
        ))}
      </div>

      <h4>Extra Skills</h4>
      <div className="skills-badges">
        {parsed.skills?.extra_skills?.map((s, i) => (
          <span className="skill-badge badge-extra" key={i}>{s}</span>
        ))}
      </div>
    </div>

 <div className="summary-block">
  <h3>AI Summary</h3>

  <div
    className="formatted-summary enhanced-summary"
    dangerouslySetInnerHTML={formatSummary(parsed.llm_analysis)}
  />
</div>



  </div>
)}

    </div>
  );
}
