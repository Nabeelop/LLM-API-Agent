import { useState } from "react";
import { api } from "../api/client";

export default function Sidebar() {
  const [status, setStatus] = useState<string>("No PDF uploaded");
  const [loading, setLoading] = useState(false);

  const uploadPdf = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files) return;

    const formData = new FormData();
    formData.append("file", e.target.files[0]);

    setLoading(true);
    setStatus("Uploading...");

    try {
      await api.post("/upload", formData);
      setStatus(`✅ ${e.target.files[0].name}`);
    } catch {
      setStatus("❌ Upload failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      width: 280,
      background: "#020617",
      padding: 16,
      borderRight: "1px solid #1e293b",
      display: "flex",
      flexDirection: "column",
      gap: 16
    }}>
      <div style={{ fontWeight: 600 }}>Knowledge Base</div>

      <label style={{
        padding: 10,
        borderRadius: 6,
        background: "#1e293b",
        textAlign: "center"
      }}>
        {loading ? "Uploading..." : "📄 Upload PDF"}
        <input
          type="file"
          hidden
          accept="application/pdf"
          onChange={uploadPdf}
        />
      </label>

      <div style={{
        fontSize: 14,
        color: "#94a3b8",
        wordBreak: "break-word"
      }}>
        {status}
      </div>

      <div style={{
        marginTop: "auto",
        fontSize: 12,
        color: "#64748b"
      }}>
        RAG • FastAPI • React • LangChain
      </div>
    </div>
  );
}
