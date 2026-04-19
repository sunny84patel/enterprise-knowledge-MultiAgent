// ui/src/components/WorkflowLog.jsx
// Shows the live agent execution trace from Repo 2

const AGENT_COLORS = {
  Router: "#7c3aed",
  Retriever: "#2563eb",
  Rewriter: "#d97706",
  FactCheck: "#059669",
  Safety: "#dc2626",
  Synthesizer: "#0891b2",
  WebSearch: "#7c3aed",
};

function getAgentName(step) {
  const match = step.match(/\[(\w+)\]/);
  return match ? match[1] : "Agent";
}

export default function WorkflowLog({ trace }) {
  return (
    <div style={{
      width: 280, borderLeft: "1px solid #e5e7eb",
      padding: 16, overflowY: "auto", background: "#fafafa",
    }}>
      <h3 style={{ margin: "0 0 12px", fontSize: 14, fontWeight: 600, color: "#374151" }}>
        Agent Execution Trace
      </h3>
      {trace.length === 0 ? (
        <p style={{ fontSize: 12, color: "#9ca3af" }}>Ask a question to see the agent trace</p>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {trace.map((step, i) => {
            const name = getAgentName(step);
            const color = AGENT_COLORS[name] || "#6b7280";
            return (
              <div key={i} style={{
                padding: "8px 10px", borderRadius: 6,
                background: "white", border: `1px solid ${color}22`,
                borderLeft: `3px solid ${color}`,
              }}>
                <div style={{ fontSize: 11, fontWeight: 600, color, marginBottom: 2 }}>
                  {name}
                </div>
                <div style={{ fontSize: 12, color: "#374151" }}>
                  {step.replace(/\[\w+\]\s*→?\s*/, "")}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
