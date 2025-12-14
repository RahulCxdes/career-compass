import { Link, useLocation } from "react-router-dom";
import "./Header.css";

export default function Header() {
  const location = useLocation();
  const isHome = location.pathname === "/";

  return (
    <header className={`header ${isHome ? "header-home" : "header-solid"}`}>
      
      <div className="header-left">
        <div className="logo-mark">CC</div>
        <div>
          <h1 className="brand-title">Career Compass</h1>
          <p className="brand-subtitle">AI-powered career assistant</p>
        </div>
      </div>

      <nav className="nav">
        <Link to="/" className="nav-link">Home</Link>
        <Link to="/analyzer" className="nav-link">Analyzer</Link>
      </nav>

      {!isHome && (
        <div className="header-right">
          <div className="status-pill">
            <span className="status-dot"></span>
            Connected
          </div>
        </div>
      )}
    </header>
  );
}
