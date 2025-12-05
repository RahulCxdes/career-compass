# chat_endpoint.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import json

import os
from groq import Groq

from chat_retrieval import retrieve_context_for_chat
from chat_prompt import CHAT_SYSTEM_PROMPT
from chat_memory import get_history, append_turn
import memory_db  # ✅ IMPORTANT: import memory db

router = APIRouter(prefix="/api", tags=["chat"])


# ---------- Models ----------
class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    target: str
    used_resume_context: bool
    used_jd_context: bool


# ---------- LLM ----------
_groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def call_chat_llm(system_prompt: str, history: List[dict], user_payload: dict):

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)

    messages.append({
        "role": "user",
        "content": (
            "Use ONLY the resume_context and jd_context provided here.\n"
            "If information is missing, say 'Not enough information'.\n\n"
            f"{json.dumps(user_payload, indent=2)}"
        )
    })

    resp = _groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        temperature=0.2,
        max_tokens=800
    )

    return resp.choices[0].message.content.strip()





# ---------- Endpoint ----------
@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest):
    if not payload.query.strip():
        raise HTTPException(400, "Query cannot be empty")

    # 1) VECTOR SEARCH
    contexts = retrieve_context_for_chat(payload.query)
    target = contexts["target"]

    resume_context = contexts["resume_context"]
    jd_context = contexts["jd_context"]

    # 2) SEND ALL DATA TO LLM (FIXED)
    user_payload = {
        "query": payload.query,
        "target": target,
        "resume_context": resume_context,
        "jd_context": jd_context,
    }



    # 3) CHAT MEMORY
    history = []
    if payload.session_id:
        for turn in get_history(payload.session_id):
            history.append({"role": turn["role"], "content": turn["content"]})

    # 4) CALL LLM
    answer = call_chat_llm(
        system_prompt=CHAT_SYSTEM_PROMPT,
        history=history,
        user_payload=user_payload
    )

    # 5) STORE CHAT MEMORY
    if payload.session_id:
        append_turn(payload.session_id, "user", payload.query)
        append_turn(payload.session_id, "assistant", answer)

    # 6) RETURN
    return ChatResponse(
        answer=answer,
        target=target,
        used_resume_context=bool(resume_context),
        used_jd_context=bool(jd_context),
    )
