// ui/src/components/ChatPanel.jsx
// Main chat interface — sends queries to FastAPI backend

import { useState, useRef, useEffect } from "react";
import WorkflowLog from "./WorkflowLog";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

export default function ChatPanel() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [agentTrace, setAgentTrace] = useState([]);
  const [showTrace, setShowTrace] = useState(false);
  const [sessionId] = useState(() => `session_${Date.now()}`);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMsg = { role: "user", content: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);
    setAgentTrace([]);

    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: input,
          session_id: sessionId,
          messages: messages,
        }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.answer, sources: data.sources },
      ]);
      setAgentTrace(data.agent_trace || []);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Error: ${err.message}`, isError: true },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div style={{ display: "flex", height: "100vh", fontFamily: "system-ui, sans-serif" }}>
      {/* Chat area */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", maxWidth: 720, margin: "0 auto" }}>
        {/* Header */}
        <div style={{ padding: "16px 24px", borderBottom: "1px solid #e5e7eb", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <h1 style={{ margin: 0, fontSize: 18, fontWeight: 600 }}>Enterprise Knowledge Agent</h1>
            <p style={{ margin: 0, fontSize: 12, color: "#6b7280" }}>Multi-Agent RAG · LangGraph · Qdrant · LlamaIndex</p>
          </div>
          <button
            onClick={() => setShowTrace(!showTrace)}
            style={{ padding: "6px 12px", borderRadius: 6, border: "1px solid #d1d5db", background: showTrace ? "#f3f4f6" : "white", cursor: "pointer", fontSize: 13 }}
          >
            {showTrace ? "Hide" : "Show"} Agent Trace
          </button>
        </div>

        {/* Messages */}
        <div style={{ flex: 1, overflowY: "auto", padding: "16px 24px" }}>
          {messages.length === 0 && (
            <div style={{ textAlign: "center", color: "#9ca3af", marginTop: 80 }}>
              <p style={{ fontSize: 16 }}>Ask anything about your knowledge base</p>
              <p style={{ fontSize: 13 }}>Upload PDFs via the /ingest endpoint first</p>
            </div>
          )}
          {messages.map((msg, i) => (
            <div key={i} style={{ marginBottom: 16, display: "flex", flexDirection: "column", alignItems: msg.role === "user" ? "flex-end" : "flex-start" }}>
              <div style={{
                maxWidth: "80%",
                padding: "10px 14px",
                borderRadius: msg.role === "user" ? "16px 16px 4px 16px" : "16px 16px 16px 4px",
                background: msg.role === "user" ? "#2563eb" : msg.isError ? "#fef2f2" : "#f9fafb",
                color: msg.role === "user" ? "white" : msg.isError ? "#dc2626" : "#111827",
                fontSize: 14,
                lineHeight: 1.6,
                border: msg.role === "assistant" ? "1px solid #e5e7eb" : "none",
              }}>
                {msg.content}
              </div>
              {msg.sources && msg.sources.length > 0 && (
                <div style={{ marginTop: 4, fontSize: 11, color: "#6b7280" }}>
                  Sources: {msg.sources.map((s, j) => (
                    <span key={j} style={{ marginRight: 8, background: "#eff6ff", color: "#1d4ed8", padding: "1px 6px", borderRadius: 4 }}>
                      {s.source || "unknown"}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
          {loading && (
            <div style={{ display: "flex", gap: 4, padding: "12px 14px", background: "#f9fafb", borderRadius: "16px 16px 16px 4px", width: "fit-content", border: "1px solid #e5e7eb" }}>
              {[0, 1, 2].map((i) => (
                <div key={i} style={{ width: 6, height: 6, borderRadius: "50%", background: "#9ca3af", animation: `bounce 1.2s ease-in-out ${i * 0.2}s infinite` }} />
              ))}
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div style={{ padding: "12px 24px", borderTop: "1px solid #e5e7eb", display: "flex", gap: 8 }}>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question... (Enter to send)"
            rows={2}
            style={{ flex: 1, padding: "10px 14px", borderRadius: 8, border: "1px solid #d1d5db", resize: "none", fontSize: 14, fontFamily: "inherit", outline: "none" }}
          />
          <button
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            style={{ padding: "0 20px", borderRadius: 8, background: loading || !input.trim() ? "#93c5fd" : "#2563eb", color: "white", border: "none", cursor: loading || !input.trim() ? "not-allowed" : "pointer", fontWeight: 600, fontSize: 14 }}
          >
            Send
          </button>
        </div>
      </div>

      {/* Agent Trace Panel */}
      {showTrace && <WorkflowLog trace={agentTrace} />}

      <style>{`@keyframes bounce { 0%,80%,100%{transform:scale(0)} 40%{transform:scale(1)} }`}</style>
    </div>
  );
}
