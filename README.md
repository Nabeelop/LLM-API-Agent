# 🤖 LLM API Agent

A full-stack RAG (Retrieval-Augmented Generation) application that lets you upload API documentation PDFs, ask natural language questions about them, and execute Python code snippets in an interactive sandbox — all powered by a HuggingFace LLM.

---

## ✨ Features

| Feature | Description |
|---|---|
| 📄 PDF Ingestion | Upload API docs and index them into a local vector store |
| 💬 RAG Chat | Ask questions — the LLM answers using only your uploaded docs as context |
| 🐍 Code Sandbox | AI-generated or manually written Python code is executed live on the backend |
| 🧠 Chat History | Last 5 exchanges are kept in context for multi-turn conversations |
| ⚡ Real-time UI | React + Vite frontend with Monaco editor, animated typing indicator, and toast notifications |

---

## 🏗️ Architecture

```
LLM API Agent/
├── app/
│   └── main.py            # FastAPI backend — /ask, /upload, /execute endpoints
├── rag/
│   ├── loader.py          # PDF loading via PyPDFLoader
│   ├── splitter.py        # API-aware recursive text splitter
│   ├── embeddings.py      # HuggingFace sentence-transformers embeddings
│   ├── retriever.py       # Chroma vector store retriever
│   └── prompt.py          # Prompt builder (chat history + retrieved docs)
├── chroma_db/             # Persisted vector store (auto-created)
├── data/pdfs/             # Uploaded PDF storage (auto-created)
└── frontend/
    └── src/
        ├── api/client.ts          # Axios API client
        ├── context/AppContext.tsx # Global state
        └── components/
            ├── sidebar/           # Document upload panel
            ├── chat/              # Chat interface
            └── sandbox/           # Python REPL sandbox
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- A [HuggingFace API token](https://huggingface.co/settings/tokens)

---

### 1. Clone & Set Up Python Environment

```bash
# Create and activate a virtual environment
python -m venv myenv
.\myenv\Scripts\activate        # Windows
# source myenv/bin/activate     # macOS/Linux

# Install Python dependencies
pip install -r requirement.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```env
HUGGINGFACEHUB_API_TOKEN=hf_your_token_here
```

> The backend uses the HuggingFace Inference API. Make sure your token has read access.

### 3. Start the Backend

```bash
# From the project root (with venv activated)
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`  
Interactive docs: `http://localhost:8000/docs`

### 4. Start the Frontend

```bash
cd frontend
npm install     # first time only
npm run dev
```

The UI will be available at `http://localhost:5173`

---

## 📡 API Reference

### `POST /upload`
Upload and index a PDF file into the vector store.

- **Body**: `multipart/form-data` with a `file` field
- **Returns**: `{ message, filename, chunks_added }`

### `POST /ask`
Ask a question using RAG over your uploaded documents.

- **Body**: `{ "query": "How do I authenticate with the Kite API?" }`
- **Returns**: `{ answer, executable, code? }`

### `POST /execute`
Execute arbitrary Python code and capture its stdout.

- **Body**: `{ "code": "print('Hello!')" }`
- **Returns**: `{ "output": "Hello!\n" }`

---

## 🛠️ How the RAG Pipeline Works

```
User Query
    │
    ▼
Chroma Vector Store ──► Top-K Retrieved Chunks
    │                           │
    └───────────────────────────┘
                │
                ▼
        build_messages()
    (system prompt + history + context + query)
                │
                ▼
    HuggingFace LLM (DeepSeek-R1-Distill)
                │
                ▼
    clean_response() ──► strip <think> blocks
                │
                ▼
    extract_code() ──► if code found, sent to Sandbox
```

---

## 🔧 Configuration

| Variable | Default | Description |
|---|---|---|
| `HUGGINGFACEHUB_API_TOKEN` | — | **Required.** Your HuggingFace token |
| Backend port | `8000` | Set via `--port` flag in uvicorn |
| Frontend port | `5173` | Set by Vite (auto-increments if busy) |
| `MAX_HISTORY` | `5` | Number of past exchanges kept in context |
| `chunk_size` | `500` | Characters per document chunk |
| `chunk_overlap` | `100` | Overlap between consecutive chunks |
| `max_new_tokens` | `1500` | Max tokens the LLM can generate per response |

---

## 📦 Tech Stack

**Backend**
- [FastAPI](https://fastapi.tiangolo.com/) — API framework
- [LangChain](https://www.langchain.com/) — RAG orchestration
- [ChromaDB](https://www.trychroma.com/) — Local vector store
- [HuggingFace](https://huggingface.co/) — LLM & embeddings (`DeepSeek-R1-Distill-Qwen-1.5B`, `all-MiniLM-L6-v2`)
- [pypdf](https://pypi.org/project/pypdf/) — PDF parsing

**Frontend**
- [React 18](https://react.dev/) + [TypeScript](https://www.typescriptlang.org/)
- [Vite](https://vitejs.dev/) — Build tool
- [Monaco Editor](https://microsoft.github.io/monaco-editor/) — VS Code-style code editor
- [Framer Motion](https://www.framer.com/motion/) — Animations
- [Tailwind CSS](https://tailwindcss.com/) — Styling
- [Sonner](https://sonner.emilkowal.ski/) — Toast notifications

---

## 🐛 Troubleshooting

**`Could not reach the backend API`**  
→ Make sure `uvicorn` is running on port 8000. Check for port conflicts with `netstat -ano | findstr :8000`.

**`PDF uploaded but no text extracted`**  
→ The PDF may be image-based (scanned). Try a text-selectable PDF instead.

**Sandbox returns no output**  
→ Ensure your code uses `print()` — `exec()` captures stdout only.

**LLM responses are slow**  
→ The HuggingFace Inference API can be slow on free tier. The frontend timeout is set to 2 minutes.

---

## 📝 License

MIT
