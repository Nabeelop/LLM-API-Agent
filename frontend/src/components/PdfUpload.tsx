import { api } from "../api/client";

export default function PdfUpload() {
  const uploadPdf = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files) return;

    const formData = new FormData();
    formData.append("file", e.target.files[0]);

    await api.post("/upload", formData);
    alert("PDF uploaded & indexed");
  };

  return (
    <label style={{
      display: "inline-block",
      padding: "8px 12px",
      border: "1px solid #ccc",
      borderRadius: 6,
      cursor: "pointer"
    }}>
      📄 Upload PDF
      <input
        type="file"
        accept="application/pdf"
        hidden
        onChange={uploadPdf}
      />
    </label>
  );
}
