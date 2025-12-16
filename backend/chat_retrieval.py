from typing import Dict

import memory_db
from intent_detection import QueryTarget, target_for_retrieval
from query_expansion import expand_query
from hybrid_retrieval import hybrid_search


def _docs_to_text(docs) -> str:
    return "\n\n---\n\n".join(
        d["text"] if isinstance(d, dict) else str(d)
        for d in docs
    )


def retrieve_context_for_chat(query: str, k: int = 3) -> Dict[str, object]:
    """
    Retrieve resume / JD context for chat using:
    - query expansion
    - hybrid retrieval (BM25 + vectors)
    - reranking
    """

    expanded_query = expand_query(query)
    target = target_for_retrieval(query)

    resume_context = ""
    jd_context = ""

    resume_chunks = []
    jd_chunks = []

    # Resume retrieval
    if target in (QueryTarget.RESUME, QueryTarget.BOTH):
        if getattr(memory_db, "resume_db", None):
            resume_chunks = hybrid_search(
                search_query=expanded_query,
                db=memory_db.resume_db,
                top_k=k,
                bm25_k=20,
                vec_k=20,
                use_rerank=True,
                section_filter=None,
            )
            resume_context = _docs_to_text(resume_chunks)

    # JD retrieval
    if target in (QueryTarget.JD, QueryTarget.BOTH):
        if getattr(memory_db, "jd_db", None):
            jd_chunks = hybrid_search(
                search_query=expanded_query,
                db=memory_db.jd_db,
                top_k=k,
                bm25_k=20,
                vec_k=20,
                use_rerank=True,
                section_filter=None,
            )
            jd_context = _docs_to_text(jd_chunks)

    return {
        "target": target.value,
        "resume_context": resume_context,
        "jd_context": jd_context,
        "resume_chunks": resume_chunks,
        "jd_chunks": jd_chunks,
    }
