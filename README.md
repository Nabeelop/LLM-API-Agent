# 🤖 LLM API Agent

An autonomous RAG-powered agent that reads unstructured API documentation and generates functional Python integration scripts — with a secure in-browser execution sandbox.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 Autonomous Script Generation | Generates ready-to-run Python integration scripts from API docs |
| 📄 PDF Ingestion | Upload API docs and index them into a ChromaDB vector store |
| 🧠 MMR Retriever (λ=0.7) | API-aware regex splitting + Jaccard dedup reduces context redundancy |
| 🔒 Secure WASM Sandbox | Pyodide-powered in-browser Python execution with import blocking and timeouts |
| 💬 Multi-turn Chat | Last 5 exchanges kept in context for conversational follow-ups |
| ⚡ Modular FastAPI Backend | Separate routers, response-time middleware, health endpoint |

---

## 🏗️ Architecture

```
LLM API Agent/
├── app/
│   ├── main.py              # FastAPI app factory (CORS, middleware, router mounting)
│   ├── dependencies.py      # Shared singletons (vector store, LLM, retriever)
│   ├── sandbox.py           # Secure code execution (AST validation, resource limits)
│   └── routes/
│       ├── ask.py           # POST /ask — RAG-powered Q&A with code extraction
│       ├── upload.py        # POST /upload — async PDF ingestion
│       ├── execute.py       # POST /execute — sandboxed code execution
│       └── health.py        # GET /health — system status & metadata
├── rag/
│   ├── loader.py            # PDF loading via PyPDFLoader
│   ├── splitter.py          # API-aware regex text splitter
│   ├── embeddings.py        # HuggingFace sentence-transformer embeddings
│   ├── retriever.py         # MMR retriever (λ=0.7) + Jaccard deduplication
│   └── prompt.py            # Autonomous agent prompt builder
├── chroma_db/               # Persisted vector store (auto-created)
├── data/pdfs/               # Uploaded PDF storage (auto-created)
└── frontend/
    └── src/
        ├── api/client.ts           # Axios API client
        ├── context/AppContext.tsx   # Global state
        └── components/
            ├── sidebar/            # Document upload panel
            ├── chat/               # Chat interface
            └── sandbox/            # Pyodide WASM sandbox with Monaco editor
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
python -m venv myenv
.\myenv\Scripts\activate        # Windows
# source myenv/bin/activate     # macOS/Linux

pip install -r requirement.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```env
HUGGINGFACEHUB_API_TOKEN=hf_your_token_here
```

### 3. Start the Backend

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`
Interactive docs: `http://localhost:8000/docs`

### 4. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

The UI will be available at `http://localhost:5173`

---

## 📡 API Reference

### `POST /ask`
Ask a question using RAG over your uploaded documents.

- **Body**: `{ "query": "How do I authenticate with this API?", "session_id": "optional" }`
- **Returns**: `{ answer, executable, code? }`

### `POST /upload`
Upload and index a PDF into the vector store (async processing).

- **Body**: `multipart/form-data` with a `file` field
- **Returns**: `{ message, filename, chunks_added }`

### `POST /execute`
Execute Python code through the secure sandbox.

- **Body**: `{ "code": "print('Hello!')" }`
- **Returns**: `{ output, blocked, blocked_reason? }`

### `GET /health`
System status and metadata.

- **Returns**: `{ status, uptime_seconds, vectorstore_documents, model, embeddings, sandbox }`

---

## 🛠️ How the RAG Pipeline Works

```
User Query
    │
    ▼
Chroma Vector Store ──► MMR Retriever (λ=0.7, k=4, fetch_k=10)
                              │
                              ▼
                    Jaccard Deduplication (threshold=0.70)
                              │
                              ▼
                    build_messages()
              (system prompt + history + context + query)
                              │
                              ▼
              HuggingFace LLM (DeepSeek-R1-Distill-Llama-8B)
                              │
                              ▼
              clean_response() ──► strip <think> blocks
                              │
                              ▼
              extract_code() ──► if code found, sent to Sandbox
```

---

## 🔒 Sandbox Security

The execution sandbox operates at two levels:

| Layer | Mechanism |
|---|---|
| **Frontend (Pyodide)** | WebAssembly isolation — no real filesystem/network access |
| **Backend (subprocess)** | AST-based import blocking, CPU timeout, env sanitization, temp dir isolation |

**Blocked imports**: `os`, `sys`, `subprocess`, `shutil`, `socket`, `http`, `ctypes`, `importlib`, `signal`, `multiprocessing`, `threading`, `pickle`, and more.

---

## 📦 Tech Stack

**Backend**
- [FastAPI](https://fastapi.tiangolo.com/) — Modular API framework with routers
- [LangChain](https://www.langchain.com/) — RAG orchestration
- [ChromaDB](https://www.trychroma.com/) — Local vector store
- [HuggingFace](https://huggingface.co/) — LLM & embeddings (`DeepSeek-R1-Distill-Llama-8B`, `bge-small-en-v1.5`)

**Frontend**
- [React 18](https://react.dev/) + [TypeScript](https://www.typescriptlang.org/)
- [Vite](https://vitejs.dev/) — Build tool
- [Pyodide](https://pyodide.org/) — In-browser Python (WebAssembly)
- [Monaco Editor](https://microsoft.github.io/monaco-editor/) — VS Code-style code editor
- [Framer Motion](https://www.framer.com/motion/) — Animations
- [Tailwind CSS](https://tailwindcss.com/) — Styling

---

## 📝 License

MIT
