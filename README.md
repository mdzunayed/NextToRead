<h1 align="center">📚 NextToRead</h1>

<p align="center">
  Find your next great read, matched to your mood.


</p>

<p align="center">
  A semantic book discovery app — describe the kind of story you want in plain
  language, filter by category and emotional tone, and get AI-matched
  recommendations powered by vector search.
</p>

---

## Preview

<!-- Drop your screenshot at docs/screenshot.png (or change the src below) -->
<p align="center">
  <img src="data/Screenshot from 2026-06-17 00-07-54.png" alt="NextToRead screenshot" width="800" />
</p>

---

## Features

- **Semantic search** — natural-language queries matched by meaning, not keywords
- **Category filter** — Fiction, Nonfiction, Children's Fiction, Children's Nonfiction
- **Emotional tone** — Happy, Surprising, Angry, Suspenseful, Sad
- **Rich results** — cover art, clean author formatting, and descriptions
- **Modern dark UI** — responsive React + Tailwind interface

## Tech Stack

| Layer     | Tools                                                            |
| --------- | --------------------------------------------------------------- |
| Frontend  | React, Vite, Tailwind CSS, lucide-react                         |
| Backend   | FastAPI, Uvicorn                                                 |
| AI / Data | ChromaDB, HuggingFace Embeddings (`all-MiniLM-L6-v2`), LangChain, pandas |

## Getting Started

### 1. Backend (FastAPI)

```bash
# from the project root
uvicorn backend.main:app --reload --port 8000
```

### 2. Frontend (React + Vite)

```bash
cd frontend/frontend
npm install
npm run dev
```

Then open **http://localhost:5173** in your browser.

> The backend must be running on port `8000` for recommendations to load.

---

