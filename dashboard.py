import os
import pandas as pd
import numpy as np
from dotenv import load_dotenv

# CHANGED: Use your local HuggingFace embeddings instead of OpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
import gradio as gr

load_dotenv()

# Load the books metadata
books = pd.read_csv("/media/zunayed/HDD_code2/book-recommender/data/books_with_emotions.csv")
books["large_thumbnail"] = books["thumbnail"] + "&fife=w800"
# books["large_thumbnail"] = np.where(
#     books["large_thumbnail"].isna(),
#     "cover-not-found.jpg",
#     books["large_thumbnail"],
# )

books["large_thumbnail"] = np.where(
    books["large_thumbnail"].isna(),
    "https://via.placeholder.com/300x400.png?text=No+Cover+Found",
    books["large_thumbnail"],
)

# CHANGED: Point directly to your pre-computed local database
PERSIST_DIR = os.path.abspath("my_local_chromadb")

print("Loading local HuggingFace embedding model...")
local_embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

print("Connecting to your existing local vector database...")
# This opens the DB instantly without re-vectorizing anything!
db_books = Chroma(
    persist_directory=PERSIST_DIR,
    embedding_function=local_embeddings
)


def retrieve_semantic_recommendations(
        query: str,
        category: str = None,
        tone: str = None,
        initial_top_k: int = 150,  # Increased from 50 to 150 to catch more category matches
        final_top_k: int = 16,
) -> pd.DataFrame:
    # If the user leaves the query empty, provide a default string so vector search doesn't panic
    if not query.strip():
        query = "highly rated interesting books"

    recs = db_books.similarity_search(query, k=initial_top_k)
    books_list = [int(rec.page_content.strip('"').split()[0]) for rec in recs]
    book_recs = books[books["isbn13"].isin(books_list)]

    # Apply category filter
    if category != "All":
        filtered_recs = book_recs[book_recs["simple_categories"] == category]

        # FALLBACK: If vector search didn't catch this category, hard-pull books from it directly
        if filtered_recs.empty:
            filtered_recs = books[books["simple_categories"] == category].head(initial_top_k)
        book_recs = filtered_recs.head(final_top_k)
    else:
        book_recs = book_recs.head(final_top_k)

    # Sort by tone if valid data exists
    if not book_recs.empty:
        if tone == "Happy" and "joy" in book_recs.columns:
            book_recs = book_recs.sort_values(by="joy", ascending=False)
        elif tone == "Surprising" and "surprise" in book_recs.columns:
            book_recs = book_recs.sort_values(by="surprise", ascending=False)
        elif tone == "Angry" and "anger" in book_recs.columns:
            book_recs = book_recs.sort_values(by="anger", ascending=False)
        elif tone == "Suspenseful" and "fear" in book_recs.columns:
            book_recs = book_recs.sort_values(by="fear", ascending=False)
        elif tone == "Sad" and "sadness" in book_recs.columns:
            book_recs = book_recs.sort_values(by="sadness", ascending=False)

    return book_recs.head(final_top_k)


def recommend_books(query: str, category: str, tone: str):
    recommendations = retrieve_semantic_recommendations(query, category, tone)
    results = []

    if recommendations.empty:
        # Return a friendly placeholder message if absolutely nothing matches
        return [("https://via.placeholder.com/300x400.png?text=No+Match+Found",
                 "No books found matching these filters. Try another phrase!")]

    for _, row in recommendations.iterrows():
        description = row.get("description", "")
        if pd.isna(description):
            description = "No description available."

        truncated_desc_split = str(description).split()
        truncated_description = " ".join(truncated_desc_split[:30]) + "..."

        authors = row.get("authors", "Unknown Author")
        if pd.isna(authors):
            authors_str = "Unknown Author"
        else:
            authors_split = str(authors).split(";")
            if len(authors_split) == 2:
                authors_str = f"{authors_split[0]} and {authors_split[1]}"
            elif len(authors_split) > 2:
                authors_str = f"{', '.join(authors_split[:-1])}, and {authors_split[-1]}"
            else:
                authors_str = str(authors)

        # Fix thumbnail image path validation
        img_url = row.get("large_thumbnail", "https://via.placeholder.com/300x400.png?text=No+Cover")
        if pd.isna(img_url) or img_url == "cover-not-found.jpg":
            img_url = "https://via.placeholder.com/300x400.png?text=No+Cover"

        caption = f"{row['title']} by {authors_str}: {truncated_description}"
        results.append((img_url, caption))

    return results

def recommend_books(
        query: str,
        category: str,
        tone: str
):
    recommendations = retrieve_semantic_recommendations(query, category, tone)
    results = []

    for _, row in recommendations.iterrows():
        description = row.get("description", "")
        # Clean fallback if description is missing/NaN
        if pd.isna(description):
            description = "No description available."

        truncated_desc_split = str(description).split()
        truncated_description = " ".join(truncated_desc_split[:30]) + "..."

        authors = row.get("authors", "Unknown Author")
        if pd.isna(authors):
            authors_str = "Unknown Author"
        else:
            authors_split = str(authors).split(";")
            if len(authors_split) == 2:
                authors_str = f"{authors_split[0]} and {authors_split[1]}"
            elif len(authors_split) > 2:
                authors_str = f"{', '.join(authors_split[:-1])}, and {authors_split[-1]}"
            else:
                authors_str = str(authors)

        caption = f"{row['title']} by {authors_str}: {truncated_description}"
        results.append((row["large_thumbnail"], caption))
    return results


categories = ["All"] + sorted(books["simple_categories"].dropna().unique().tolist())
tones = ["All"] + ["Happy", "Surprising", "Angry", "Suspenseful", "Sad"]

# UI Design Layout
with gr.Blocks(theme=gr.themes.Glass()) as dashboard:
    gr.Markdown("# Semantic Book Recommender")

    with gr.Row():
        user_query = gr.Textbox(label="Please enter a description of a book:",
                                placeholder="e.g., A story about forgiveness")
        category_dropdown = gr.Dropdown(choices=categories, label="Select a category:", value="All")
        tone_dropdown = gr.Dropdown(choices=tones, label="Select an emotional tone:", value="All")
        submit_button = gr.Button("Find recommendations")

    gr.Markdown("## Recommendations")
    output = gr.Gallery(label="Recommended books", columns=8, rows=2)

    submit_button.click(fn=recommend_books,
                        inputs=[user_query, category_dropdown, tone_dropdown],
                        outputs=output)

if __name__ == "__main__":
    dashboard.launch()