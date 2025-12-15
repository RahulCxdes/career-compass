import { BrowserRouter as Router, Routes, Route, useLocation } from "react-router-dom";
import Header from "./pages/Header";
import Home from "./pages/Home";
import Analyzer from "./pages/Analyzer";
import "./App.css";

export default function App() {
  return (
    <Router>
      <PageWrapper />
    </Router>
  );
}

function PageWrapper() {
  const location = useLocation();
  const isAnalyzer = location.pathname === "/analyzer";

  return (
    <>
      <Header />

      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/analyzer" element={<Analyzer />} />
      </Routes>

      {/* Chatbot only in analyzer page */}
      {isAnalyzer && <AnalyzerChat />}
    </>
  );
}

function AnalyzerChat() {
  const ChatDrawer = require("./pages/ChatDrawer").default;
  return <ChatDrawer />;
}

