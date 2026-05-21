from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from data_loader import get_product_search_data
from llm_answer import generate_answer
from metadata_extractor import extract_metadata_filters
from retriever import retrieve_products
from schemas import SearchRequest, SearchResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_product_search_data()
    yield


app = FastAPI(title="Hybrid Retail Product Search RAG", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    data = get_product_search_data()
    return {
        "status": "ok",
        "products": len(data.df),
        "search_rows": len(data.search_index),
    }


@app.post("/search", response_model=SearchResponse)
def search(request: SearchRequest):
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    try:
        _, metadata_trace = extract_metadata_filters(query)
        top_products = retrieve_products(query, metadata_trace, top_k=10)
        answer = generate_answer(query, top_products)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return SearchResponse(
        query=query,
        answer=answer,
        metadata_trace=metadata_trace,
        top_products=top_products,
    )

