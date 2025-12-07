# ============================================================
# chat_endpoint.py
# Fully optimized, history-aware RAG chat module
# ============================================================

from fastapi import APIRouter
from pydantic import BaseModel
from groq import Groq
import memory_db
from hybrid_retrieval import hybrid_search

router = APIRouter()

# -------------------------------
# Conversation Memory in RAM
# Only stores real messages
# -------------------------------
CHAT_HISTORY = []  # last 12 turns


# -------------------------------
# Groq Client Helper
# -------------------------------
def get_client():
    import os
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GROQ_API_KEY")
    return Groq(api_key=api_key)


# -------------------------------
# Query Rewriter (History-Aware)
# -------------------------------
def rewrite_query(history, user_input):
    """
    Converts ambiguous queries into explicit ones.
    Example:
      user: "improve that"
      → "improve the machine learning classification project in the resume"
    """
    client = get_client()

    # Use only last 6 messages for context
    convo = "\n".join([f"{m['role']}: {m['content']}" for m in history[-6:]])

    prompt = f"""
Rewrite the user's message into a clear, stand-alone search query.
Use the conversation history to resolve pronouns or vague references.

Conversation History:
{convo}

User message:
{user_input}

Return ONLY the rewritten query. No explanations. No formatting.
"""

    resp = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=60,
        temperature=0.2,
    )
    return resp.choices[0].message.content.strip()


# -------------------------------
# Chat Request Schema
# -------------------------------
class ChatRequest(BaseModel):
    message: str


# -------------------------------
# MAIN CHAT ENDPOINT
# -------------------------------
@router.post("/chat")
async def chat(req: ChatRequest):
    global CHAT_HISTORY

    user_msg = req.message
    CHAT_HISTORY.append({"role": "user", "content": user_msg})

    # -------------------------------------------------------
    # STEP 1 — Rewrite Query using history (but DO NOT store)
    # -------------------------------------------------------
    rewritten = rewrite_query(CHAT_HISTORY, user_msg)

    # -------------------------------------------------------
    # STEP 2 — Retrieve context from Resume/JD DBs
    # -------------------------------------------------------
    resume_db = memory_db.resume_db
    jd_db = memory_db.jd_db

    resume_chunks = []
    jd_chunks = []

    if resume_db:
        resume_chunks = hybrid_search(
            search_query=rewritten,
            db=resume_db,
            top_k=3,
            use_rerank=True,
        )

    if jd_db:
        jd_chunks = hybrid_search(
            search_query=rewritten,
            db=jd_db,
            top_k=3,
            use_rerank=True,
        )

    # Convert chunks to simple text blocks
    resume_text = "\n".join(
        [c["text"] if isinstance(c, dict) else str(c) for c in resume_chunks]
    )
    jd_text = "\n".join(
        [c["text"] if isinstance(c, dict) else str(c) for c in jd_chunks]
    )

    # -------------------------------------------------------
    # STEP 3 — Build final prompt for LLM
    # -------------------------------------------------------
    prompt = f"""
You are a career assistant AI.

Use ONLY the provided Resume Context and JD Context to answer the user's question.
Do NOT hallucinate details not present in context.

User Question:
{user_msg}

Rewritten Query (for retrieval):
{rewritten}

Resume Context:
{resume_text or "NO RESUME CONTEXT FOUND"}

JD Context:
{jd_text or "NO JD CONTEXT FOUND"}
"""

    # -------------------------------------------------------
    # STEP 4 — LLM Final Response
    # -------------------------------------------------------
    client = get_client()
    resp = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        temperature=0.4,
    )

    answer = resp.choices[0].message.content.strip()

    # Save assistant reply into chat history
    CHAT_HISTORY.append({"role": "assistant", "content": answer})

    # Keep history short
    CHAT_HISTORY = CHAT_HISTORY[-12:]

    # Frontend response
    return {
        "answer": answer,
        "rewritten_query": rewritten,
        "used_resume_context": resume_chunks,
        "used_jd_context": jd_chunks,
    }
