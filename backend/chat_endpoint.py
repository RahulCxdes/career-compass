
from fastapi import APIRouter
from pydantic import BaseModel
from groq import Groq
import memory_db
from hybrid_retrieval import hybrid_search
from history_rewrite import rewrite_query
from chat_retrieval import retrieve_context_for_chat


router = APIRouter()

CHAT_HISTORY = [] 

def get_client():
    import os
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GROQ_API_KEY")
    return Groq(api_key=api_key)



class ChatRequest(BaseModel):
    message: str


@router.post("/chat")
async def chat(req: ChatRequest):
    global CHAT_HISTORY

    user_msg = req.message
    CHAT_HISTORY.append({"role": "user", "content": user_msg})


    rewritten = rewrite_query(CHAT_HISTORY, user_msg)


    retrieval = retrieve_context_for_chat(rewritten, k=3)

    resume_text = retrieval["resume_context"]
    jd_text = retrieval["jd_context"]

    resume_chunks = resume_text
    jd_chunks = jd_text



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


    client = get_client()
    resp = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        temperature=0.4,
    )

    answer = resp.choices[0].message.content.strip()


    CHAT_HISTORY.append({"role": "assistant", "content": answer})


    CHAT_HISTORY = CHAT_HISTORY[-12:]


    return {
        "answer": answer,
        "rewritten_query": rewritten,
        "resume_retrieved_chunks": retrieval.get("resume_chunks", []),
        "jd_retrieved_chunks": retrieval.get("jd_chunks", []),
    }
