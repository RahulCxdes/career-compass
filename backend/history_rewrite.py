"""
Rewrite user query based on conversation history.
Makes chatbot retrieval history-aware WITHOUT changing intent
and ensures rewritten queries are retrieval-friendly.
"""

from groq import Groq
import os


def get_groq_client():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("❌ GROQ_API_KEY not set.")
    return Groq(api_key=api_key)


def rewrite_query(history: list, user_message: str) -> str:
    """
    Rewrites the user's message using conversation history.

    CRITICAL BEHAVIOR:
    - Preserve original intent
    - Do NOT introduce comparison unless explicitly asked
    - Do NOT introduce role requirements unless explicitly asked
    - MUST produce a retrieval-usable query
    """

    if not history:
        return user_message

    client = get_groq_client()

    history_text = "\n".join(
        [f"{h['role']}: {h['content']}" for h in history]
    )

    prompt = f"""
You are a query rewriter inside a RAG chatbot.

Your task is to rewrite the user's latest message into a clear,
standalone search query that will be used for document retrieval.

STRICT RULES (DO NOT BREAK):
- Preserve the user's original intent exactly.
- Do NOT introduce comparison words such as "compare", "gap",
  "missing", or "requirements" unless the user explicitly asks for them.
- If the user asks about readiness or suitability in a GENERAL sense
  (e.g., "am I ready for frontend roles"), focus ONLY on the candidate.
- When rewriting readiness or suitability questions, ALWAYS include
  candidate-focused terms such as:
    • skills
    • experience
    • background
    • projects
- Only introduce comparison or role expectations if the user explicitly
  asks about:
    • missing skills
    • gaps
    • readiness for THIS job
    • comparison with expectations
- Use conversation history ONLY to resolve vague references
  like "that", "those", or "it".
- Do NOT answer the question.
- Return ONLY the rewritten query.

Conversation History:
{history_text}

User message:
"{user_message}"

Rewrite it into a standalone, retrieval-optimized query:
"""

    resp = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=80,
        temperature=0.0,
    )

    rewritten = resp.choices[0].message.content.strip()

    # Safety fallback
    if len(rewritten) < 3:
        return user_message

    return rewritten
