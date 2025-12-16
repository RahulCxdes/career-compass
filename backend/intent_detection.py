from enum import Enum
from groq import Groq
import os


class QueryTarget(str, Enum):
    RESUME = "resume"
    JD = "jd"
    BOTH = "both"


def _get_groq_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set")
    return Groq(api_key=api_key)


def target_for_retrieval(query: str) -> QueryTarget:


    client = _get_groq_client()

    prompt = f"""
You are an intent classifier inside a RAG system.

Decide which context is required to answer the user's query.

STRICT RULES:
- If the query asks about the user's readiness, suitability, strengths,
  or background in a GENERAL sense (e.g., "am I ready for frontend roles"),
  WITHOUT asking about requirements or comparison → resume
- If the query asks what is required, expected, or needed for a role → jd
- If the query explicitly asks about:
  • missing skills
  • gaps
  • comparison
  • readiness for THIS job
  → both

User query:
"{query}"

Answer with ONLY one word:
resume
jd
both
"""

    resp = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=5,
    )

    decision = resp.choices[0].message.content.strip().lower()

    if decision == "resume":
        return QueryTarget.RESUME
    if decision == "jd":
        return QueryTarget.JD
    return QueryTarget.BOTH
