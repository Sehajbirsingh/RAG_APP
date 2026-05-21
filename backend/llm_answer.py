import os

import requests


OLLAMA_GENERATE_URL = os.getenv("OLLAMA_GENERATE_URL", "http://localhost:11434/api/generate")
ANSWER_MODEL = os.getenv("ANSWER_MODEL", "qwen3:4b")


def format_retrieved_products(products: list[dict]) -> str:
    blocks = []

    for index, product in enumerate(products, start=1):
        description_text = product.get("description_text") or ""
        attribute_text = product.get("attribute_text") or "No attribute data available."

        block = f"""
Product {index}
Product UID: {product.get("product_uid")}
Title: {product.get("product_title")}
Matched Source: {product.get("source")}
Similarity Score: {product.get("score", 0):.4f}

Description:
{description_text}

Attributes:
{attribute_text}
"""
        blocks.append(block.strip())

    return "\n\n---\n\n".join(blocks)


def build_answer_prompt(query: str, products: list[dict]) -> str:
    retrieved_products_text = format_retrieved_products(products)

    return f"""
You are a retail product recommendation assistant.

Your job is to answer the exact user query below using ONLY the retrieved product records provided.

USER QUERY:
\"\"\"
{query}
\"\"\"

RETRIEVED PRODUCT RECORDS:
{retrieved_products_text}

The user query may be:
1. A product recommendation request
2. A general product question
3. A suitability check, such as "is this good for X?"
4. A comparison between retrieved products

First, identify the user's intent.

Treat these as hard constraints when clearly stated, which could include something like:
- product type
- material
- size or dimensions
- application/use case
- indoor/outdoor use
- installation type
- capacity/power/technical requirement
- brand, if mentioned
- color/finish, if mentioned

Important:
If the user says "something similar to", "like", "close to", "alternative to", "good for", "preferably", or uses flexible wording, treat that requirement as a soft preference, not a strict hard constraint.

Hard constraints override similarity score.
Soft preferences guide the recommendation but should not automatically reject a product.

If a product violates a clearly stated hard constraint, do not recommend it as the best match.
If no retrieved product satisfies all hard constraints, say that clearly and recommend the closest available option only if it is still useful.

Do not invent product details.
Do not use outside knowledge.
If the retrieved data does not mention something, say it is unclear.
Do not say that the user query is missing; the user query is provided above inside USER QUERY.
Do not include hidden reasoning, analysis notes, or <think> tags.

Respond in this structure:

1. Best answer:
- Give the direct answer or best product recommendation.

2. Why this fits:
- Explain using evidence from the retrieved product description and attributes.

3. Requirement check:
- List the main hard constraints and soft preferences from the user query.
- Mark each as satisfied, missing, unclear, or partially matched.

4. Other relevant options:
- Mention up to 2 alternatives if useful.
- Explain briefly why they are weaker or different.

5. Final recommendation:
- Give a short plain-language final suggestion.
"""


def sanitize_answer(text: str) -> str:
    if not text:
        return ""

    think_end = text.rfind("</think>")
    if think_end != -1:
        text = text[think_end + len("</think>") :]

    return text.strip()


def generate_answer(query: str, products: list[dict]) -> str:
    if not products:
        return "No matching products were retrieved, so I cannot make a grounded recommendation."

    response = requests.post(
        OLLAMA_GENERATE_URL,
        json={
            "model": ANSWER_MODEL,
            "prompt": build_answer_prompt(query, products),
            "stream": False,
            "think": False,
            "options": {
                "temperature": 0.2,
                "top_p": 0.9,
            },
        },
        timeout=300,
    )
    response.raise_for_status()
    data = response.json()
    answer = sanitize_answer(data.get("response") or "")
    return answer or "The model did not return a final answer."
