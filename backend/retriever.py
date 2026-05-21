import os
from typing import Any

import numpy as np
import pandas as pd
import requests

from data_loader import get_product_search_data
from metadata_extractor import should_use_metadata_filter


OLLAMA_EMBED_URL = os.getenv("OLLAMA_EMBED_URL", "http://localhost:11434/api/embed")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "mxbai-embed-large")
MIN_FILTERED_ROWS = 5


def embed_texts(texts: list[str]) -> list[list[float]]:
    response = requests.post(
        OLLAMA_EMBED_URL,
        json={"model": EMBEDDING_MODEL, "input": texts},
        timeout=300,
    )
    response.raise_for_status()

    data = response.json()
    embeddings = data["embeddings"]
    if len(embeddings) != len(texts):
        raise ValueError(f"Expected {len(texts)} embeddings, got {len(embeddings)}")

    return embeddings


def apply_metadata_filter(df: pd.DataFrame, trace: dict) -> pd.DataFrame:
    filtered_df = df.copy()

    if trace.get("brand"):
        filtered_df = filtered_df[
            filtered_df["Brand"].astype(str).str.contains(
                str(trace["brand"]), case=False, na=False
            )
        ]

    if trace.get("color"):
        filtered_df = filtered_df[
            filtered_df["Color"].astype(str).str.contains(
                str(trace["color"]), case=False, na=False
            )
        ]

    if trace.get("material"):
        filtered_df = filtered_df[
            filtered_df["Material"].astype(str).str.contains(
                str(trace["material"]), case=False, na=False
            )
        ]

    return filtered_df


def _normalize_query_embedding(query: str) -> np.ndarray:
    query_embedding = np.array(embed_texts([query])[0], dtype=np.float32)
    return query_embedding / np.clip(np.linalg.norm(query_embedding), 1e-12, None)


def _clean_value(value: Any):
    if pd.isna(value):
        return None
    if isinstance(value, np.generic):
        return value.item()
    return value


def _records_for_response(results: pd.DataFrame) -> list[dict]:
    records = []
    for row in results.itertuples(index=False):
        records.append(
            {
                "product_uid": _clean_value(row.product_uid),
                "product_title": _clean_value(row.product_title),
                "description_text": _clean_value(row.description_text),
                "attribute_text": _clean_value(row.attribute_text),
                "source": _clean_value(row.source),
                "score": float(row.score),
                "brand": _clean_value(row.Brand),
                "color": _clean_value(row.Color),
                "material": _clean_value(row.Material),
                "category": _clean_value(row.category),
                "sub_id": _clean_value(row.sub_id),
                "category_id": _clean_value(row.category_id),
            }
        )
    return records


def retrieve_products(query: str, metadata_trace: dict, top_k: int = 10) -> list[dict]:
    data = get_product_search_data()
    df = data.df
    candidate_uids = None

    metadata_trace["original_count"] = int(len(df))

    if should_use_metadata_filter(metadata_trace):
        candidate_df = apply_metadata_filter(df, metadata_trace)
        metadata_trace["filtered_count"] = int(len(candidate_df))

        if len(candidate_df) < MIN_FILTERED_ROWS:
            metadata_trace["decision"] = "FALLBACK to normal cosine search"
            metadata_trace["fallback_used"] = True
            candidate_df = df
        else:
            candidate_uids = set(candidate_df["product_uid"].tolist())
    else:
        metadata_trace["filtered_count"] = None
        candidate_df = df

    metadata_trace["candidate_count"] = int(len(candidate_df))

    query_embedding = _normalize_query_embedding(query)

    if candidate_uids is None:
        active_index = data.search_index
        active_matrix = data.search_matrix
    else:
        mask = data.search_index["product_uid"].isin(candidate_uids).to_numpy()
        if not mask.any():
            metadata_trace["decision"] = "FALLBACK to normal cosine search"
            metadata_trace["fallback_used"] = True
            active_index = data.search_index
            active_matrix = data.search_matrix
        else:
            active_index = data.search_index.loc[mask].reset_index(drop=True)
            active_matrix = data.search_matrix[mask]

    scores = active_matrix @ query_embedding

    results = active_index[["product_uid", "product_title", "source"]].copy()
    results["score"] = scores
    results = (
        results.sort_values("score", ascending=False)
        .drop_duplicates(subset="product_uid", keep="first")
        .head(top_k)
    )

    meta_cols = [
        "product_uid",
        "description_text",
        "attribute_text",
        "Brand",
        "Color",
        "Material",
        "category",
        "sub_id",
        "category_id",
    ]
    results = results.merge(df[meta_cols], on="product_uid", how="left")

    return _records_for_response(results)

