import { useMemo, useState } from "react";
import {
  AlertCircle,
  Boxes,
  BrainCircuit,
  Filter,
  Loader2,
  PackageSearch,
  Search,
  User,
  Sparkles,
} from "lucide-react";

import AnswerPanel from "./components/AnswerPanel.jsx";
import ProductCard from "./components/ProductCard.jsx";
import TracePanel from "./components/TracePanel.jsx";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const examples = [
  "I need a durable wooden corner post for an outdoor residential fence that can be painted or stained.",
  "Find a chrome Delta shower faucet trim kit.",
  "Looking for something that improves cutting speed and finish quality for a renovation project.",
];

function App() {
  const [query, setQuery] = useState("");
  const [submittedQuery, setSubmittedQuery] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const products = result?.top_products || [];
  const trace = result?.metadata_trace;

  const statusText = useMemo(() => {
    if (isLoading) return "Searching";
    if (result) return `${products.length} products`;
    return "Ready";
  }, [isLoading, products.length, result]);

  async function runSearch(event) {
    event?.preventDefault();
    const cleanQuery = query.trim();
    if (!cleanQuery) return;

    setIsLoading(true);
    setError("");
    setSubmittedQuery(cleanQuery);
    setResult(null);
    setQuery("");

    try {
      const response = await fetch(`${API_BASE_URL}/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: cleanQuery }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Search failed.");
      }

      setResult(data);
    } catch (searchError) {
      setError(searchError.message);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="app-shell">
      <section className="hero-band">
        <div className="hero-copy">
          <div className="eyebrow">
            <PackageSearch size={18} aria-hidden="true" />
            Hybrid Retail RAG
          </div>
          <h1>Metadata-aware product search</h1>
        </div>

        <div className="status-pill" aria-live="polite">
          {isLoading ? <Loader2 className="spin" size={18} aria-hidden="true" /> : <Sparkles size={18} aria-hidden="true" />}
          {statusText}
        </div>
      </section>

      {error && (
        <section className="error-panel" role="alert">
          <AlertCircle size={20} aria-hidden="true" />
          <span>{error}</span>
        </section>
      )}

      {submittedQuery && (
        <section className="submitted-query" aria-label="Submitted query">
          <div className="query-avatar">
            <User size={18} aria-hidden="true" />
          </div>
          <p>{submittedQuery}</p>
        </section>
      )}

      <section className="results-grid">
        <div className="answer-column">
          <AnswerPanel answer={result?.answer} isLoading={isLoading} />
          <TracePanel trace={trace} isLoading={isLoading} />
        </div>

        <div className="products-column">
          <div className="section-title">
            <Boxes size={20} aria-hidden="true" />
            <h2>Retrieved Products</h2>
          </div>

          {isLoading ? (
            <div className="loading-block products-loading">
              <Loader2 className="spin" size={26} aria-hidden="true" />
              <span>Retrieving products</span>
            </div>
          ) : products.length === 0 ? (
            <div className="empty-panel">
              <Filter size={22} aria-hidden="true" />
              <span>No products loaded yet.</span>
            </div>
          ) : (
            <div className="product-list">
              {products.map((product, index) => (
                <ProductCard
                  key={`${product.product_uid}-${product.source}`}
                  product={product}
                  rank={index + 1}
                />
              ))}
            </div>
          )}
        </div>
      </section>

      <section className="search-band">
        <form className="search-console" onSubmit={runSearch}>
          <div className="example-row">
            {examples.map((example) => (
              <button
                className="example-chip"
                key={example}
                type="button"
                onClick={() => setQuery(example)}
                title={example}
              >
                {example}
              </button>
            ))}
          </div>

          <div className="composer-row">
            <div className="query-field">
              <Search size={20} aria-hidden="true" />
              <textarea
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                rows={2}
                placeholder="Ask for a product, brand, color, material, or use case..."
              />
            </div>

            <button className="search-button" type="submit" disabled={isLoading || !query.trim()}>
              {isLoading ? <Loader2 className="spin" size={20} aria-hidden="true" /> : <BrainCircuit size={20} aria-hidden="true" />}
              Search
            </button>
          </div>
        </form>
      </section>
    </main>
  );
}

export default App;
