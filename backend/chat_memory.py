# chat_memory.py
from typing import Dict, List, TypedDict


class ChatTurn(TypedDict):
    role: str   # "user" or "assistant"
    content: str


# Very simple process-level memory: {session_id: [ChatTurn, ...]}
CHAT_SESSIONS: Dict[str, List[ChatTurn]] = {}


def get_history(session_id: str) -> List[ChatTurn]:
    return CHAT_SESSIONS.get(session_id, [])


def append_turn(session_id: str, role: str, content: str) -> None:
    if not session_id:
        return  # no memory if no session id
    CHAT_SESSIONS.setdefault(session_id, []).append(
        ChatTurn(role=role, content=content)
    )
    # Keep only last N turns
    if len(CHAT_SESSIONS[session_id]) > 20:
        CHAT_SESSIONS[session_id] = CHAT_SESSIONS[session_id][-20:]
