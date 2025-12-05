# query_expansion.py
import os
from groq import Groq

_groq = Groq(api_key=os.getenv("GROQ_API_KEY"))

def expand_query(user_query: str) -> str:
    prompt = f"""
Rewrite the following user query into a search-optimized query for semantic retrieval.
Make it explicit, skill-focused, and context-rich.

User query: "{user_query}"

Return ONLY the rewritten query.
"""

    resp = _groq.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=50
    )

    return resp.choices[0].message.content.strip()
