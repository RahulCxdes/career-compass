# chat_retrieval.py
from typing import Dict, List

import memory_db
from intent_detection import QueryTarget, target_for_retrieval

from query_expansion import expand_query
from hybrid_retrieval import hybrid_search


def _docs_to_text(docs: List[str]) -> str:
    return "\n\n---\n\n".join(docs)


def retrieve_context_for_chat(query: str, k: int = 3) -> Dict[str, str]:
    """
    Retrieve resume/JD context for chat using:
      - LLM query expansion
      - Hybrid retrieval (BM25 + embeddings)
      - Cross-encoder reranking
    """


    expanded_query = expand_query(query)


    target = target_for_retrieval(query)

    resume_context = ""
    jd_context = ""

    if target in (QueryTarget.RESUME, QueryTarget.BOTH):
        if getattr(memory_db, "resume_db", None):
            best_docs = hybrid_search(
                search_query=expanded_query,
                db=memory_db.resume_db,
                top_k=k,
                bm25_k=20,
                vec_k=20,
                use_rerank=True,
                section_filter=None,  # for now use all sections
            )
            resume_context = _docs_to_text(best_docs)

    if target in (QueryTarget.JD, QueryTarget.BOTH):
        if getattr(memory_db, "jd_db", None):
            best_docs = hybrid_search(
                search_query=expanded_query,
                db=memory_db.jd_db,
                top_k=k,
                bm25_k=20,
                vec_k=20,
                use_rerank=True,
                section_filter=None,
            )
            jd_context = _docs_to_text(best_docs)

    return {
        "target": target.value,
        "resume_context": resume_context,
        "jd_context": jd_context,
    }
