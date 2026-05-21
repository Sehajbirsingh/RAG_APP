from typing import Any, Optional

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)


class ProductResult(BaseModel):
    product_uid: int | str
    product_title: str
    description_text: Optional[str] = None
    attribute_text: Optional[str] = None
    source: str
    score: float
    brand: Optional[str] = None
    color: Optional[str] = None
    material: Optional[str] = None
    category: Optional[str] = None
    sub_id: Optional[int | str] = None
    category_id: Optional[int | str] = None


class SearchResponse(BaseModel):
    query: str
    answer: str
    thinking: Optional[str] = None
    metadata_trace: dict[str, Any]
    top_products: list[ProductResult]
