// ui/src/components/UploadKnowledge.jsx
// PDF / text upload UI — calls the /ingest FastAPI endpoint

import { useState } from "react";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

export default function UploadKnowledge() {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState(null);
  const [uploading, setUploading] = useState(false);

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setStatus(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API_URL}/ingest`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      setStatus({ ok: res.ok, message: data.message || data.detail });
    } catch (err) {
      setStatus({ ok: false, message: err.message });
    } finally {
      setUploading(false);
      setFile(null);
    }
  };

  return (
    <div style={{ padding: 24, maxWidth: 480 }}>
      <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>Upload Knowledge Document</h2>

      <div
        style={{
          border: "2px dashed #d1d5db", borderRadius: 8, padding: "32px 24px",
          textAlign: "center", cursor: "pointer", background: file ? "#eff6ff" : "white",
        }}
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => { e.preventDefault(); setFile(e.dataTransfer.files[0]); }}
      >
        <input
          type="file"
          accept=".pdf,.txt"
          style={{ display: "none" }}
          id="file-input"
          onChange={(e) => setFile(e.target.files[0])}
        />
        <label htmlFor="file-input" style={{ cursor: "pointer" }}>
          {file ? (
            <span style={{ color: "#2563eb", fontWeight: 500 }}>{file.name}</span>
          ) : (
            <span style={{ color: "#6b7280" }}>Drop PDF or TXT here, or click to browse</span>
          )}
        </label>
      </div>

      <button
        onClick={handleUpload}
        disabled={!file || uploading}
        style={{
          marginTop: 12, width: "100%", padding: "10px 0",
          background: !file || uploading ? "#93c5fd" : "#2563eb",
          color: "white", border: "none", borderRadius: 8,
          fontWeight: 600, fontSize: 14, cursor: !file || uploading ? "not-allowed" : "pointer",
        }}
      >
        {uploading ? "Uploading & Indexing..." : "Upload & Index"}
      </button>

      {status && (
        <div style={{
          marginTop: 12, padding: "10px 14px", borderRadius: 6,
          background: status.ok ? "#f0fdf4" : "#fef2f2",
          color: status.ok ? "#166534" : "#dc2626",
          fontSize: 13,
        }}>
          {status.message}
        </div>
      )}
    </div>
  );
}
