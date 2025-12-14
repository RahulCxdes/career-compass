"""
Rewrite user query based on conversation history.
Makes chatbot retrieval history-aware.
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
    If no rewriting needed, returns original query.
    """

    if not history:
        return user_message

    client = get_groq_client()

    history_text = "\n".join([f"{h['role']}: {h['content']}" for h in history])

    prompt = f"""
You are a query rewriter inside a RAG chatbot.

Task:
- Rewrite the user's latest message into a self-contained search query.
- Use the conversation history to understand references like "that project", "those skills", "improve it", etc.
- Do NOT answer the question.
- Only rewrite it into a complete query for retrieval purposes.

Conversation History:
{history_text}

User message:
"{user_message}"

Rewrite it into a standalone, explicit query:
"""

    resp = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100,
        temperature=0.0,
    )

    rewritten = resp.choices[0].message.content.strip()

    if len(rewritten) < 3:
        return user_message

    return rewritten
