# 🧠 MemChat — AI Chat with Persistent Memory

> Built with [Mem0](https://mem0.ai) · Gemini 2.5 Flash · Qdrant · FastAPI · React

MemChat is a full-stack AI chatbot that **remembers you across sessions** using Mem0's memory layer. Unlike standard chatbots that forget everything when you close the tab, MemChat extracts meaningful facts from your conversations and recalls them the next time you chat — automatically.

---

## ✨ What makes this interesting

Most AI chat apps are stateless. Every session starts from zero. MemChat solves this with Mem0:

- **Automatic memory extraction** — Mem0 reads each conversation turn and decides what's worth remembering (preferences, facts, context)
- **Semantic search at inference time** — before every LLM response, the top-5 most relevant memories are retrieved and injected into the system prompt
- **Memory compounds over time** — the more you chat, the more personalized responses become
- **Per-user isolation** — memories are scoped to a `user_id`, making it multi-user ready

---

## 🏗 Architecture

```
User Message
     │
     ▼
FastAPI Backend
     │
     ├── Mem0.search(query, user_id)     ← semantic memory retrieval (Qdrant)
     │        │
     │        ▼
     │   Relevant Memories
     │        │
     ├── Build system prompt             ← inject memories into Gemini context
     │
     ├── Gemini 2.5 Flash                ← generate response
     │
     └── Mem0.add([user, assistant])     ← persist new turn as memories
              │
              ▼
         Qdrant (on-disk)                ← vector store, gemini-embedding-001
```

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| **Memory** | [Mem0](https://mem0.ai) |
| **LLM** | Google Gemini 2.5 Flash (free tier) |
| **Embeddings** | Gemini `gemini-embedding-001` (768-dim) |
| **Vector Store** | Qdrant (local, on-disk — no server needed) |
| **Backend** | Python, FastAPI |
| **Frontend** | React, Vite, Tailwind CSS |

---

## 🚀 Running locally

### Prerequisites
- Python 3.10+
- Node.js 18+
- A free [Google AI Studio API key](https://aistudio.google.com/app/apikey)

### Backend

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/MemChat-Mem0Demo.git
cd MemChat-Mem0Demo

# Create and activate virtual environment
python -m venv memenv
memenv\Scripts\activate        # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Add your GEMINI_API_KEY to .env

# Start the backend
python main.py
# → Running at http://localhost:8000
# → API docs at http://localhost:8000/docs
```

### Frontend

```bash
cd memchat-frontend
npm install
npm run dev
# → Running at http://localhost:5173
```

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/chat` | Send a message, get a memory-aware reply |
| `GET` | `/api/memories/{user_id}` | Fetch all stored memories for a user |
| `DELETE` | `/api/memories/{user_id}` | Wipe all memories for a user |
| `DELETE` | `/api/memories/{user_id}/{memory_id}` | Delete a single memory |
| `GET` | `/health` | Health check |

### Example request

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "rahul",
    "message": "I love hiking and I prefer vegetarian food",
    "history": []
  }'
```

```json
{
  "reply": "That's a great combination! Hiking and vegetarian eating go well together...",
  "memories_used": [],
  "memories_added": {
    "results": [
      {"id": "abc123", "memory": "Likes hiking", "event": "ADD"},
      {"id": "def456", "memory": "Prefers vegetarian food", "event": "ADD"}
    ]
  }
}
```

---

## 🧪 Seeing memory in action

1. Start a session with user ID `rahul`
2. Tell MemChat something personal: *"I'm a software engineer based in Texas and I love hiking"*
3. Close the browser tab completely
4. Reopen and start a new session with the same user ID `rahul`
5. Ask: *"What do you know about me?"* or just ask for hiking recommendations
6. Watch it recall what you told it — without any session state

The memory panel on the right side of the UI shows exactly what Mem0 has extracted and stored in real time.

---

## 📁 Project Structure

```
MemChat-Mem0Demo/
├── main.py                  # FastAPI app, CORS, lifespan
├── memory_service.py        # Mem0 wrapper (add/search/get_all/delete)
├── chat_service.py          # Gemini LLM + memory injection
├── routers/
│   ├── chat.py              # POST /api/chat
│   └── memory.py            # GET/DELETE /api/memories
├── requirements.txt
├── .env.example
└── memchat-frontend/
    ├── src/
    │   ├── App.jsx          # Main UI — chat + memory panel
    │   └── api.js           # Axios client
    └── package.json
```

---

## 🔧 Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | ✅ | Google AI Studio API key |
| `QDRANT_PATH` | optional | Path for Qdrant on-disk storage (default: `./qdrant_storage`) |
| `QDRANT_COLLECTION` | optional | Qdrant collection name (default: `memchat`) |
| `ALLOWED_ORIGINS` | optional | CORS origins (default: `localhost:3000,localhost:5173`) |
| `PORT` | optional | Backend port (default: `8000`) |

---

## 💡 How Mem0 works here

Each chat turn goes through this memory lifecycle:

1. **Search** — `mem.search(user_message, user_id=user_id, limit=5)` retrieves semantically similar past memories using Qdrant vector search
2. **Inject** — retrieved memories are formatted into the Gemini system prompt so the model has personal context
3. **Add** — after the reply is generated, `mem.add([user_turn, assistant_turn], user_id=user_id)` extracts new facts and stores them as embeddings in Qdrant
4. **Deduplicate** — Mem0 handles conflicting or duplicate memories automatically (e.g. if you say you moved cities, it updates the old memory)

---

*Built by [Rahul Tandon](https://linkedin.com/in/rahultandon98)*
