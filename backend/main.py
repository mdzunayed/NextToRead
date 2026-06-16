"""
uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

import os
from typing import List, Optional

import numpy as np
import pandas as pd
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from pydantic import BaseModel

# Repo root = the parent of this file's directory (backend/main.py -> repo root).
# Derived from __file__ so it works regardless of where uvicorn is launched from.
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH   = os.path.join(BASE_DIR, "data", "books_with_emotions.csv")
CHROMA_DIR = os.path.abspath(os.path.join(BASE_DIR, "my_local_chromadb"))

app = FastAPI(title="Semantic Book Recommender", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("📚  Loading books metadata…")
books: pd.DataFrame = pd.read_csv(CSV_PATH)

books["large_thumbnail"] = np.where(
    books["thumbnail"].isna(),
    "https://via.placeholder.com/300x400.png?text=No+Cover+Found",
    books["thumbnail"].astype(str) + "&fife=w800",
)

print("Loading HuggingFace embedding model (all-MiniLM-L6-v2)…")
local_embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

print(f"🗄️   Connecting to existing Chroma DB at {CHROMA_DIR}…")
db_books = Chroma(
    persist_directory=CHROMA_DIR,
    embedding_function=local_embeddings,
)
print("Ready.")
TONE_COLUMN: dict[str, str] = {
    "Happy":       "joy",
    "Surprising":  "surprise",
    "Angry":       "anger",
    "Suspenseful": "fear",
    "Sad":         "sadness",
}

class BookCard(BaseModel):
    title: str
    authors: str
    description: str
    image_url: str


class MetaResponse(BaseModel):
    categories: List[str]
    tones: List[str]


class RecommendResponse(BaseModel):
    books: List[BookCard]


def _parse_authors(raw) -> str:
    """Turn a semicolon-delimited authors string into readable prose."""
    if pd.isna(raw):
        return "Unknown Author"
    parts = [p.strip() for p in str(raw).split(";") if p.strip()]
    if len(parts) == 0:
        return "Unknown Author"
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return f"{parts[0]} and {parts[1]}"
    return f"{', '.join(parts[:-1])}, and {parts[-1]}"


def _to_book_card(row: pd.Series) -> BookCard:
    desc = row.get("description", "")
    if pd.isna(desc) or str(desc).strip() == "":
        desc = "No description available."

    img = row.get("large_thumbnail", "")
    if pd.isna(img) or img in ("cover-not-found.jpg", ""):
        img = "https://via.placeholder.com/300x400.png?text=No+Cover+Found"

    return BookCard(
        title=str(row.get("title", "Untitled")),
        authors=_parse_authors(row.get("authors")),
        description=str(desc),
        image_url=str(img),
    )


def _retrieve(
    query: str,
    category: Optional[str],
    tone: Optional[str],
    initial_top_k: int = 150,
    final_top_k: int = 16,
) -> pd.DataFrame:
    # Graceful fallback for empty query
    effective_query = query.strip() if query and query.strip() else "highly rated interesting books"

    # Vector search
    recs = db_books.similarity_search(effective_query, k=initial_top_k)
    isbn_list = [int(r.page_content.strip('"').split()[0]) for r in recs]
    book_recs = books[books["isbn13"].isin(isbn_list)].copy()

    # Category filter with fallback
    if category and category != "All":
        filtered = book_recs[book_recs["simple_categories"] == category]
        if filtered.empty:
            # Hard-pull from the full dataset for that category
            filtered = books[books["simple_categories"] == category].head(initial_top_k).copy()
        book_recs = filtered

    # Tone sort
    if tone and tone != "All":
        col = TONE_COLUMN.get(tone)
        if col and col in book_recs.columns:
            book_recs = book_recs.sort_values(by=col, ascending=False)

    return book_recs.head(final_top_k)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/api/meta", response_model=MetaResponse)
def get_meta() -> MetaResponse:
    """Return available categories and emotional tones for the UI dropdowns."""
    raw_cats = books["simple_categories"].dropna().unique().tolist()
    categories = ["All"] + sorted(raw_cats)
    tones = ["All", "Happy", "Surprising", "Angry", "Suspenseful", "Sad"]
    return MetaResponse(categories=categories, tones=tones)


@app.get("/api/recommend", response_model=RecommendResponse)
def get_recommendations(
    query:    str           = Query(default="",    description="Free-text description of a book"),
    category: Optional[str] = Query(default="All", description="Book category filter"),
    tone:     Optional[str] = Query(default="All", description="Emotional tone filter"),
) -> RecommendResponse:
    """Return up to 16 semantically matched book recommendations."""
    frame = _retrieve(query, category, tone)

    if frame.empty:
        return RecommendResponse(books=[])

    return RecommendResponse(
        books=[_to_book_card(row) for _, row in frame.iterrows()]
    )