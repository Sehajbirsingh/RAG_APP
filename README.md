# Retail RAG App

React + FastAPI web app for a hybrid retail product-search RAG prototype. The app uses the precomputed `embedding` dataframe, local Ollama models, metadata-aware filtering, vector similarity search, and a React chat-style UI.

## Current Pipeline

```text
User query
  -> FastAPI /search
  -> metadata extraction: brand / color / material
  -> optional dataframe filtering
  -> Ollama query embedding
  -> cosine similarity retrieval
  -> top products
  -> final Ollama answer
  -> React UI
```

## Backend

Run from the project root:

```bash
cd /Users/temp/Documents/Retail_RAG
.venv/bin/pip install -r RAG_APP/backend/requirements.txt
.venv/bin/uvicorn app:app --app-dir RAG_APP/backend --host 0.0.0.0 --port 8000
```


### `app.py`

FastAPI entry point. It exposes `/health` and `/search`, then coordinates the full RAG pipeline.

```python
_, metadata_trace = extract_metadata_filters(query)
top_products = retrieve_products(query, metadata_trace, top_k=10)
answer_payload = generate_answer(query, top_products)
```

### `metadata_extractor.py`

Uses local Ollama `qwen3:4b` to extract only:

- `brand`
- `color`
- `material`

It returns a trace used by retrieval:

```python
trace = {
    "brand": result.brand,
    "color": result.color,
    "material": result.material,
    "metadata_step_used": use_metadata_filter,
    "decision": "USE metadata filtering" if use_metadata_filter else "SKIP metadata filtering",
}
```

Pydantic validates the LLM JSON output so malformed metadata responses do not break the app.

### `retriever.py`

Applies metadata filtering when useful, then runs cosine similarity over the dataframe embeddings.

```python
if should_use_metadata_filter(metadata_trace):
    candidate_df = apply_metadata_filter(df, metadata_trace)

query_embedding = _normalize_query_embedding(query)
scores = active_matrix @ query_embedding
```

Filtering uses dataframe columns such as `Brand`, `Color`, and `Material`. If filtering returns too few rows, retrieval falls back to the full dataframe.

### `data_loader.py`

Loads an embedded df built of a combined search index from:

- `description_embedding`
- `attribute_embedding`

It caches the loaded dataframe so the data is not reloaded on every query.

```python
@lru_cache(maxsize=1)
def get_product_search_data() -> ProductSearchData:
    df = pd.read_pickle(path)
```

### `llm_answer.py`

Formats retrieved products and asks local Ollama `qwen3:4b` to generate the final answer. The backend currently sends the top 5 retrieved products to the final LLM for speed, while the UI display the top 10 matched products.

```python
prompt = build_answer_prompt(query, products[:MAX_PRODUCTS_FOR_ANSWER])
save_last_prompt(prompt)
```

The exact final prompt is saved to:

```text
RAG_APP/backend/last_llm_prompt.txt
```

### `schemas.py`

Defines request and response contracts with Pydantic.

```python
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)

class SearchResponse(BaseModel):
    query: str
    answer: str
    metadata_trace: dict[str, Any]
    top_products: list[ProductResult]
```

## Frontend

Run from the frontend folder:

```bash
cd /Users/temp/Documents/Retail_RAG/RAG_APP/frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

The React UI includes:

- fixed bottom search box
- chat-style search history
- metadata trace panel
- answer panel with markdown rendering
- thinking toggle
- retrieved-products drawer
- response timer

## Main Libraries

- **FastAPI**: exposes Python RAG logic as a web API.
- **Pydantic**: validates API payloads and LLM metadata JSON.
- **Pandas**: loads and filters the product dataframe.
- **NumPy**: handles embedding vectors and cosine similarity.
- **Requests**: calls local Ollama endpoints.
- **Ollama**: runs local embedding and answer models.
- **React**: interactive frontend state, chat history, product drawer, and loading states.

## Work In Progress

### History-Aware Queries

Planned next step: add a query resolver before metadata extraction.

```text
current query + recent chat history
  -> standalone resolved query
  -> metadata extractor
  -> retriever
```

Example:

```text
Previous: I need a saw blade for better finish quality.
Current: I want it in black.
Resolved: black saw blade for better finish quality.
```

Standalone queries should remain unchanged.

### Search MCP Product Enrichment

Planned next step: use Search MCP to search retrieved product titles on the web and enrich product cards with:

- clickable product/page links
- product images when available
- source site
- match confidence

This should happen after retrieval and should not replace the core dataframe/vector search.

### LangChain

LangChain is not required for the current working app. It will be implemented later as an orchestration layer for:

- history-aware query rewriting
- MCP tool use

The current core retrieval path remains intentionally simple and explainable.
