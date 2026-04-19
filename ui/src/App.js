import { useState } from "react";
import ChatPanel from "./components/ChatPanel";
import UploadKnowledge from "./components/UploadKnowledge";

export default function App() {
  const [tab, setTab] = useState("chat");

  return (
    <div style={{ minHeight: "100vh", background: "#f9fafb" }}>
      {/* Nav */}
      <nav style={{
        background: "white", borderBottom: "1px solid #e5e7eb",
        padding: "0 24px", display: "flex", gap: 0, alignItems: "center"
      }}>
        {["chat", "upload"].map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            style={{
              padding: "14px 20px", border: "none", background: "none",
              borderBottom: tab === t ? "2px solid #2563eb" : "2px solid transparent",
              color: tab === t ? "#2563eb" : "#6b7280",
              fontWeight: tab === t ? 600 : 400,
              fontSize: 14, cursor: "pointer", textTransform: "capitalize",
            }}
          >
            {t === "chat" ? "💬 Chat" : "📄 Upload Knowledge"}
          </button>
        ))}
      </nav>

      {/* Content */}
      {tab === "chat" ? <ChatPanel /> : <UploadKnowledge />}
    </div>
  );
}
