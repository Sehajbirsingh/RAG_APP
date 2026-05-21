from functools import lru_cache
import json
import os
import re
from typing import Literal, Optional

import requests
from pydantic import BaseModel, Field


class MetadataFilters(BaseModel):
    brand: Optional[str] = Field(
        default=None,
        description="Brand explicitly mentioned in the query, such as Samsung, BEHR, Delta, Whirlpool.",
    )
    color: Optional[str] = Field(
        default=None,
        description="Color explicitly mentioned in the query, such as black, white, chrome, brown, bronze, gray.",
    )
    material: Optional[str] = Field(
        default=None,
        description="Material explicitly mentioned in the query, such as aluminum, steel, wood, plastic, composite, stainless steel.",
    )
    confidence: Literal["high", "medium", "low"] = Field(
        description="Confidence that brand, color, or material was clearly extracted from the query."
    )
    has_metadata_filters: bool = Field(
        description="True only if brand, color, or material was clearly mentioned."
    )


OLLAMA_GENERATE_URL = os.getenv("OLLAMA_GENERATE_URL", "http://localhost:11434/api/generate")
METADATA_MODEL = os.getenv("METADATA_MODEL", "qwen3:4b")


def _parse_json_object(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


@lru_cache(maxsize=128)
def _extract_with_ollama(query: str) -> MetadataFilters:
    prompt = f"""
/no_think
Extract metadata filters from this retail product search query.

Return only JSON with these exact fields:
- brand
- color
- material
- confidence
- has_metadata_filters

Only extract these fields:
- brand
- color
- material

Do not extract product type, category, subcategory, use case, dimensions, or general intent.
Do not guess.

Set confidence to one of: high, medium, low.
Set has_metadata_filters to true only if brand, color, or material is clearly mentioned.
If no brand, color, or material is clearly mentioned, set:
- brand = null
- color = null
- material = null
- confidence = low
- has_metadata_filters = false

Query:
{query}
"""

    response = requests.post(
        OLLAMA_GENERATE_URL,
        json={
            "model": METADATA_MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "think": False,
            "options": {"temperature": 0},
        },
        timeout=60,
    )
    response.raise_for_status()

    data = response.json()
    payload = _parse_json_object(data.get("response") or data.get("thinking") or "{}")
    return MetadataFilters.model_validate(payload)
    

def extract_metadata_filters(query: str):
    try:
        result = _extract_with_ollama(query)
    except Exception as exc:
        result = MetadataFilters(
            brand=None,
            color=None,
            material=None,
            confidence="low",
            has_metadata_filters=False,
        )
        extraction_error = str(exc)
    else:
        extraction_error = None

    use_metadata_filter = (
        result.has_metadata_filters
        and result.confidence in ["high", "medium"]
        and any([result.brand, result.color, result.material])
    )

    trace = {
        "query": query,
        "brand": result.brand,
        "color": result.color,
        "material": result.material,
        "confidence": result.confidence,
        "has_metadata_filters": result.has_metadata_filters,
        "metadata_step_used": use_metadata_filter,
        "decision": "USE metadata filtering" if use_metadata_filter else "SKIP metadata filtering",
        "fallback_used": False,
    }

    if extraction_error:
        trace["metadata_error"] = extraction_error

    return result, trace


def should_use_metadata_filter(trace: dict) -> bool:
    return (
        trace["metadata_step_used"] is True
        and trace["confidence"] in ["high", "medium"]
        and any([trace.get("brand"), trace.get("color"), trace.get("material")])
    )
