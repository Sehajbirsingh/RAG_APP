import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd


EMBEDDING_DIMENSION = 1024
DEFAULT_DATA_PATH = Path(__file__).resolve().parents[2] / "product_embeddings_final.pkl"


@dataclass(frozen=True)
class ProductSearchData:
    df: pd.DataFrame
    search_index: pd.DataFrame
    search_matrix: np.ndarray


def _data_path() -> Path:
    return Path(os.getenv("PRODUCT_DATA_PATH", DEFAULT_DATA_PATH)).expanduser().resolve()


def to_vector(value):
    if isinstance(value, np.ndarray):
        vector = value.astype(np.float32)
    elif isinstance(value, list):
        vector = np.array(value, dtype=np.float32)
    else:
        return None

    if vector.shape[0] != EMBEDDING_DIMENSION:
        return None

    return vector


def _build_source_index(df: pd.DataFrame, text_col: str, embedding_col: str, source: str):
    index = df[
        [
            "product_uid",
            "product_title",
            text_col,
            embedding_col,
        ]
    ].copy()

    index = index.rename(
        columns={
            text_col: "search_text",
            embedding_col: "embedding",
        }
    )
    index["source"] = source
    index["embedding"] = index["embedding"].apply(to_vector)
    index = index[index["embedding"].notna()].reset_index(drop=True)

    return index


def _normalize_matrix(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    return matrix / np.clip(norms, 1e-12, None)


@lru_cache(maxsize=1)
def get_product_search_data() -> ProductSearchData:
    path = _data_path()
    if not path.exists():
        raise FileNotFoundError(f"Could not find product data file: {path}")

    df = pd.read_pickle(path)

    desc_index = _build_source_index(
        df,
        text_col="description_text",
        embedding_col="description_embedding",
        source="description",
    )
    attr_index = _build_source_index(
        df,
        text_col="attribute_text",
        embedding_col="attribute_embedding",
        source="attribute",
    )

    search_index = pd.concat([desc_index, attr_index], ignore_index=True)
    search_matrix = np.vstack(search_index["embedding"].values).astype(np.float32)
    search_matrix = _normalize_matrix(search_matrix)
    search_index = search_index.drop(columns=["embedding"])

    return ProductSearchData(
        df=df,
        search_index=search_index,
        search_matrix=search_matrix,
    )

