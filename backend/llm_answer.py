import os
from pathlib import Path

import requests


OLLAMA_GENERATE_URL = os.getenv("OLLAMA_GENERATE_URL", "http://localhost:11434/api/generate")
ANSWER_MODEL = os.getenv("ANSWER_MODEL", "qwen3:4b")
LAST_PROMPT_PATH = Path(__file__).with_name("last_llm_prompt.txt")
MAX_PRODUCTS_FOR_ANSWER = 5


def format_retrieved_products(products: list[dict]) -> str:
    blocks = []

    for product in products:
        description_text = product.get("description_text") or "No description available."

        block = f"""
Title: {product.get("product_title")}
UID: {product.get("product_uid")}
Matched Source: {product.get("source")}
Similarity Score: {product.get("score", 0):.4f}

Description:
{description_text}
"""
        blocks.append(block.strip())

    return "\n\n---\n\n".join(blocks)


def build_answer_prompt(query: str, products: list[dict]) -> str:
    retrieved_products_text = format_retrieved_products(products)

    return f"""
You are a retail product recommendation assistant.

Your job is to answer the user's query using ONLY the retrieved product records provided below.

The user's intent can be:
1. A product recommendation request
2. A general product question
3. A suitability check, such as "is this good for X?"
4. A comparison between retrieved products

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
The final answer must not include hidden reasoning, analysis notes, or <think> tags.
Do not refer to products as "Product 1", "Product 2", or by list position. Use the product title and UID.
Do not include comparison tables or discuss every retrieved product.

Retrieved products:
{retrieved_products_text}

User query:
{query}

First, identify the user's intent from the User query text immediately above.

Respond in this structure:

1. Best recommendation:
- Start directly with the best product title and UID.
- Give the direct recommendation.

2. Why this fits:
- Explain why it matches the user's query.
- Use evidence from the retrieved product description.
- Mention relevant use cases, material, finish, size, durability, or installation details when available.

3. Alternatives:
- Mention up to 2 relevant alternatives if useful.
- Use each alternative's product title and UID.
- Give a brief one-line reason why each alternative may be worth considering.

4. Follow-up:
- End with one natural follow-up question only if it would help the user choose.
"""


def save_last_prompt(prompt: str) -> None:
    LAST_PROMPT_PATH.write_text(prompt, encoding="utf-8")


def split_answer_and_thinking(text: str, thinking: str | None = None) -> dict[str, str | None]:
    if not text:
        return {"answer": "", "thinking": thinking.strip() if thinking else None}

    think_end = text.rfind("</think>")
    if think_end != -1:
        think_start = text.find("<think>")
        if think_start != -1:
            thinking = text[think_start + len("<think>") : think_end].strip()
        else:
            thinking = text[:think_end].strip()
        text = text[think_end + len("</think>") :]

    return {
        "answer": text.strip(),
        "thinking": thinking.strip() if thinking else None,
    }


def generate_answer(query: str, products: list[dict]) -> dict[str, str | None]:
    if not products:
        return {
            "answer": "No matching products were retrieved, so I cannot make a grounded recommendation.",
            "thinking": None,
        }

    prompt = build_answer_prompt(query, products[:MAX_PRODUCTS_FOR_ANSWER])
    save_last_prompt(prompt)

    response = requests.post(
        OLLAMA_GENERATE_URL,
        json={
            "model": ANSWER_MODEL,
            "prompt": prompt,
            "stream": False,
            "think": True,
            "options": {
                "temperature": 0.2,
                "top_p": 0.9,
            },
        },
        timeout=300,
    )
    response.raise_for_status()
    data = response.json()
    payload = split_answer_and_thinking(
        data.get("response") or "",
        thinking=data.get("thinking"),
    )
    payload["answer"] = payload["answer"] or "The model did not return a final answer."
    return payload
