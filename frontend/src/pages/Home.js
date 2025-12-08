import { useState } from "react";
import { Link } from "react-router-dom";

export default function Home() {
  const [openCard, setOpenCard] = useState(null);

  const tips = [
    {
      title: "Strong Bullet Points",
      short: "Use action verbs.",
      details: [
        "Start with strong verbs: built, designed, developed",
        "End with measurable results",
        "Keep bullets short & crisp"
      ]
    },
    {
      title: "Tailor to JD",
      short: "Match keywords.",
      details: [
        "Highlight matching tech stack",
        "Reorder skills based on JD",
        "Mention relevant projects first"
      ]
    },
    {
      title: "ATS-Friendly",
      short: "Avoid images.",
      details: [
        "Use simple fonts",
        "Use standard headings",
        "Keep formatting clean"
      ]
    },
    {
      title: "Show Skills Clearly",
      short: "Easy to scan.",
      details: [
        "Group skills by category",
        "Keep technical skills on top",
        "Avoid long paragraphs"
      ]
    },
    {
      title: "Use Metrics",
      short: "Numbers speak.",
      details: [
        "Mention % improvements",
        "Add real performance numbers",
        "Quantify impact"
      ]
    },
    {
      title: "Clean Layout",
      short: "Consistent spacing.",
      details: [
        "One font throughout",
        "Equal spacing between sections",
        "Avoid colorful formatting"
      ]
    }
  ];

  return (
    <div className="home-container">

     <section className="hero-section">
  <div className="hero-text">

    {/* TAG */}
    <p className="eyebrow">Career Launchpad</p>

    {/* NEW CATCHY QUOTE */}
    <h2 className="hero-title large">
      Build a resume that opens doors.
    </h2>

    {/* SUBTITLE */}
    <p className="hero-subtitle large">
      AI-powered analysis that helps you improve your resume, match job descriptions, 
      and level up your career.
    </p>

    {/* BUTTON */}
    <div className="hero-actions">
      <Link to="/analyzer" className="primary-btn large-btn">
        Start Analyzing →
      </Link>
    </div>

    {/* META TAGS */}
    <div className="hero-meta large-meta">
      <span>AI insights</span>
      <span>Skill-gap detection</span>
      <span>Career guidance</span>
    </div>
  </div>
</section>

      {/* TIP CARDS */}
      <section className="tips-section">
        <h3 className="section-title big">Improve your resume</h3>

        <div className="tips-grid">
          {tips.map((tip, index) => (
            <div
              key={index}
              className={`tip-card interactive ${openCard === index ? "open" : ""}`}
              onClick={() => setOpenCard(openCard === index ? null : index)}
            >
              <h4>{tip.title}</h4>
              <p>{tip.short}</p>

              {openCard === index && (
                <ul className="tip-details">
                  {tip.details.map((d, i) => (
                    <li key={i}>{d}</li>
                  ))}
                </ul>
              )}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
