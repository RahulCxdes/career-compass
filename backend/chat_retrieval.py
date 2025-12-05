# chat_retrieval.py
from typing import Dict, List
from langchain_core.documents import Document

import memory_db
from intent_detection import QueryTarget, target_for_retrieval

from query_expansion import expand_query
from reranker import rerank


def _docs_to_text(docs: List[str]) -> str:
    return "\n\n---\n\n".join(docs)


def retrieve_context_for_chat(query: str, k: int = 3) -> Dict[str, str]:

    # 1️⃣ Query Expansion
    expanded_query = expand_query(query)

    target = target_for_retrieval(query)

    resume_context = ""
    jd_context = ""

    # 2️⃣ Retrieve & Rerank Resume Context
    if target in (QueryTarget.RESUME, QueryTarget.BOTH):
        if memory_db.resume_db:
            raw_docs = memory_db.resume_db.similarity_search(expanded_query, k=20)

            raw_texts = [d.page_content for d in raw_docs]

            best_docs = rerank(expanded_query, raw_texts, top_k=k)

            resume_context = _docs_to_text(best_docs)

    # 3️⃣ Retrieve & Rerank JD Context
    if target in (QueryTarget.JD, QueryTarget.BOTH):
        if memory_db.jd_db:
            raw_docs = memory_db.jd_db.similarity_search(expanded_query, k=20)

            raw_texts = [d.page_content for d in raw_docs]

            best_docs = rerank(expanded_query, raw_texts, top_k=k)

            jd_context = _docs_to_text(best_docs)

    return {
        "target": target.value,
        "resume_context": resume_context,
        "jd_context": jd_context,
    }
