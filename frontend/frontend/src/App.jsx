import { useState, useEffect, useCallback } from "react";
import {
  BookOpen,
  Search,
  Loader2,
  BookMarked,
  Sparkles,
  ServerCrash,
  LibraryBig,
} from "lucide-react";

const API_BASE = "http://127.0.0.1:8000";
const FALLBACK_IMG =
  "https://via.placeholder.com/300x450.png?text=No+Cover+Found";


const FALLBACK_CATEGORIES = [
  "All",
  "Fiction",
  "Nonfiction",
  "Children's Fiction",
  "Children's Nonfiction",
];
const FALLBACK_TONES = [
  "All",
  "Happy",
  "Surprising",
  "Angry",
  "Suspenseful",
  "Sad",
];
function SkeletonCard() {
  return (
    <div className="rounded-xl overflow-hidden bg-slate-800 border border-slate-700 animate-pulse">
      <div className="aspect-[2/3] bg-slate-700" />
      <div className="p-4 space-y-3">
        <div className="h-4 bg-slate-700 rounded w-4/5" />
        <div className="h-3 bg-slate-700/70 rounded w-3/5" />
        <div className="h-3 bg-slate-700/70 rounded w-full" />
        <div className="h-3 bg-slate-700/70 rounded w-5/6" />
      </div>
    </div>
  );
}

function BookCard({ book }) {
  const [imgSrc, setImgSrc] = useState(book.image_url || FALLBACK_IMG);

  return (
    <article className="group flex flex-col rounded-xl overflow-hidden bg-slate-800 border border-slate-700 hover:border-sky-500 hover:shadow-lg hover:shadow-sky-500/10 transition-all duration-300">
      {/* Cover */}
      <div className="relative aspect-[2/3] overflow-hidden bg-slate-900">
        <img
          src={imgSrc}
          alt={book.title}
          onError={() => setImgSrc(FALLBACK_IMG)}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
          loading="lazy"
        />
      </div>

      {/* Text */}
      <div className="flex flex-col flex-1 p-4 gap-1.5">
        <h3 className="text-base font-bold text-slate-100 leading-snug line-clamp-2">
          {book.title}
        </h3>
        <p className="text-sm text-sky-400 font-medium line-clamp-1">
          {book.authors}
        </p>
        <p className="text-sm text-slate-400 leading-relaxed line-clamp-3 mt-1">
          {book.description}
        </p>
      </div>
    </article>
  );
}

function StyledSelect({ label, value, onChange, options, icon: Icon }) {
  return (
    <div className="flex flex-col gap-2 min-w-0">
      <label className="text-sm font-semibold text-slate-300 flex items-center gap-2">
        {Icon && <Icon size={16} className="text-sky-400" />}
        {label}
      </label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full bg-slate-900 border border-slate-700 text-slate-100 text-base rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-sky-500 transition-colors cursor-pointer"
      >
        {options.map((opt) => (
          <option key={opt} value={opt} className="bg-slate-900 text-slate-100">
            {opt}
          </option>
        ))}
      </select>
    </div>
  );
}

//main
export default function App() {
  // Meta state — seeded with hardcoded fallbacks so dropdowns are never blank
  const [categories, setCategories] = useState(FALLBACK_CATEGORIES);
  const [tones, setTones] = useState(FALLBACK_TONES);

  // Form state
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("All");
  const [tone, setTone] = useState("All");

  // Results state
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [error, setError] = useState(null);

  // Fetch meta on mount — fall back to hardcoded options if the backend is down
  useEffect(() => {
    fetch(`${API_BASE}/api/meta`)
      .then((r) => {
        if (!r.ok) throw new Error(`Meta request failed: ${r.status}`);
        return r.json();
      })
      .then((data) => {
        setCategories(data.categories?.length ? data.categories : FALLBACK_CATEGORIES);
        setTones(data.tones?.length ? data.tones : FALLBACK_TONES);
      })
      .catch((err) => {
        console.warn(
          "⚠️ Could not load /api/meta — using hardcoded dropdown fallbacks.",
          err
        );
        setCategories(FALLBACK_CATEGORIES);
        setTones(FALLBACK_TONES);
      });
  }, []);

  const handleSearch = useCallback(async () => {
    setLoading(true);
    setSearched(true);
    setError(null);
    setBooks([]);

    try {
      const params = new URLSearchParams({ query, category, tone });
      const res = await fetch(`${API_BASE}/api/recommend?${params}`);
      if (!res.ok) throw new Error(`Server error ${res.status}`);
      const data = await res.json();
      setBooks(data.books ?? []);
    } catch (err) {
      console.error("Recommendation request failed:", err);
      setError(true);
    } finally {
      setLoading(false);
    }
  }, [query, category, tone]);

  // Allow Enter key to trigger search from the text input
  const handleKeyDown = (e) => {
    if (e.key === "Enter") handleSearch();
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 font-sans">
      {/* ── Header / Hero ── */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur">
        <div className="max-w-6xl mx-auto px-6 py-16 md:py-20 flex flex-col items-center text-center gap-5">
          <LibraryBig size={44} className="text-sky-400" strokeWidth={1.75} />
          <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight text-white">
            Next<span className="text-sky-400">To</span>Read
          </h1>
          <p className="text-lg md:text-xl text-slate-400 max-w-xl">
            Find your next great read, matched to your mood.
          </p>
        </div>
      </header>

      {/* ── Main ── */}
      <main className="max-w-6xl mx-auto px-6 py-10 space-y-12">
        {/* Search Panel */}
        <section className="bg-slate-800/60 border border-slate-700 rounded-2xl p-6 sm:p-8 shadow-xl">
          {/* Query input */}
          <div className="flex flex-col gap-2 mb-6">
            <label className="text-sm font-semibold text-slate-300 flex items-center gap-2">
              <Search size={16} className="text-sky-400" />
              Describe a book
            </label>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="e.g., A story about redemption and loss set in post-war Europe…"
              className="w-full bg-slate-900 border border-slate-700 text-slate-100 placeholder-slate-500 text-base rounded-lg px-4 py-3.5 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-sky-500 transition-colors"
            />
          </div>

          {/* Dropdowns */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 mb-8">
            <StyledSelect
              label="Category"
              value={category}
              onChange={setCategory}
              options={categories}
              icon={BookMarked}
            />
            <StyledSelect
              label="Emotional tone"
              value={tone}
              onChange={setTone}
              options={tones}
              icon={Sparkles}
            />
          </div>

          {/* Submit */}
          <button
            onClick={handleSearch}
            disabled={loading}
            className="w-full flex items-center justify-center gap-2.5 bg-sky-600 hover:bg-sky-500 disabled:opacity-60 disabled:cursor-not-allowed text-white font-bold text-base rounded-lg py-4 transition-colors focus:outline-none focus:ring-2 focus:ring-sky-400 focus:ring-offset-2 focus:ring-offset-slate-800"
          >
            {loading ? (
              <>
                <Loader2 size={18} className="animate-spin" />
                Finding recommendations…
              </>
            ) : (
              <>
                <Search size={18} />
                Find recommendations
              </>
            )}
          </button>
        </section>

        {/* ── Results Area ── */}

        {/* Backend-unreachable warning card */}
        {error && (
          <div className="rounded-2xl border border-amber-500/40 bg-amber-500/10 p-6 sm:p-8">
            <div className="flex items-start gap-4">
              <ServerCrash size={28} className="text-amber-400 shrink-0 mt-0.5" />
              <div className="space-y-3">
                <h3 className="text-lg font-bold text-amber-300">
                  Couldn't reach the recommendation server
                </h3>
                <p className="text-slate-300 leading-relaxed">
                  The FastAPI backend at{" "}
                  <code className="px-1.5 py-0.5 rounded bg-slate-800 text-amber-200 text-sm">
                    {API_BASE}
                  </code>{" "}
                  isn't responding. Start it from the project root with:
                </p>
                <pre className="bg-slate-950 border border-slate-700 rounded-lg p-4 text-sm text-sky-300 overflow-x-auto">
                  uvicorn backend.main:app --reload --port 8000
                </pre>
                <p className="text-slate-400 text-sm">
                  Then run your search again.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Loading skeletons */}
        {loading && (
          <section aria-busy="true">
            <h2 className="text-sm font-semibold text-slate-400 mb-5 uppercase tracking-wider">
              Searching…
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
              {Array.from({ length: 8 }).map((_, i) => (
                <SkeletonCard key={i} />
              ))}
            </div>
          </section>
        )}

        {/* Empty state */}
        {!loading && searched && books.length === 0 && !error && (
          <section className="flex flex-col items-center gap-4 py-20 text-center">
            <BookOpen size={52} className="text-slate-600" />
            <p className="text-xl font-bold text-slate-200">No matches found</p>
            <p className="text-slate-400 max-w-md">
              Try rephrasing your description, or broaden the category and tone
              filters.
            </p>
          </section>
        )}

        {/* Results grid */}
        {!loading && books.length > 0 && (
          <section>
            <h2 className="text-sm font-semibold text-slate-400 mb-5 uppercase tracking-wider">
              {books.length} recommendation{books.length !== 1 ? "s" : ""}
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
              {books.map((book, idx) => (
                <BookCard key={`${book.title}-${idx}`} book={book} />
              ))}
            </div>
          </section>
        )}
      </main>

      {/* ── Footer ── */}
      <footer className="border-t border-slate-800 mt-16 py-10 text-center text-sm text-slate-500">
        @Zunayed
      </footer>
    </div>
  );
}
