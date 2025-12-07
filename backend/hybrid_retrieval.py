# hybrid_retrieval.py
"""
HYBRID RETRIEVAL ENGINE
-----------------------
Returns:
- chunk text
- section name
- metadata
- bm25 or reranker score

Supports:
- BM25 keyword matching
- Vector similarity (Chroma)
- Section filtering
- Cross-encoder reranking
"""

from typing import List, Dict, Optional
from rank_bm25 import BM25Okapi
from langchain_chroma import Chroma

from reranker import rerank  # updated cross-encoder returning scores


# -------------------------------------------------------------
# Helper: Get corpus with optional section filtering
# -------------------------------------------------------------
def _get_filtered_corpus(db: Chroma, section_filter: Optional[str] = None):
    raw = db._collection.get()
    docs = raw.get("documents", [])
    metas = raw.get("metadatas", [{} for _ in docs])

    valid_indices = [
        i for i in range(len(docs))
        if section_filter is None or metas[i].get("section") == section_filter
    ]

    corpus_texts = [docs[i] for i in valid_indices]
    corpus_metas = [metas[i] for i in valid_indices]

    return corpus_texts, corpus_metas


# -------------------------------------------------------------
# Helper: Build BM25
# -------------------------------------------------------------
def _build_bm25(corpus_texts: List[str]) -> BM25Okapi:
    tokens = [doc.lower().split() for doc in corpus_texts]
    return BM25Okapi(tokens)


# -------------------------------------------------------------
# MAIN HYBRID SEARCH FUNCTION
# -------------------------------------------------------------
def hybrid_search(
    search_query: str,
    db: Chroma,
    top_k: int = 5,
    bm25_k: int = 20,
    vec_k: int = 20,
    use_rerank: bool = True,
    section_filter: Optional[str] = None,
) -> List[Dict]:

    if db is None:
        return []

    # STEP 1 → Get corpus
    corpus_texts, corpus_metas = _get_filtered_corpus(db, section_filter)
    if not corpus_texts:
        return []

    # STEP 2 → BM25
    bm25 = _build_bm25(corpus_texts)
    query_tokens = search_query.lower().split()
    bm25_scores = bm25.get_scores(query_tokens)

    bm25_ranked = sorted(
        zip(corpus_texts, corpus_metas, bm25_scores),
        key=lambda x: x[2],
        reverse=True
    )[:bm25_k]

    # STEP 3 → Vector similarity
    filter_dict = {"section": section_filter} if section_filter else None

    try:
        vec_docs = db.similarity_search_with_score(search_query, k=vec_k, filter=filter_dict)
        vec_ranked = [(d.page_content, d.metadata, float(score)) for (d, score) in vec_docs]
    except:
        vec_ranked = []

    # STEP 4 → Merge unique candidates
    candidates = bm25_ranked + vec_ranked

    seen = set()
    unique = []
    for text, meta, score in candidates:
        if text not in seen:
            seen.add(text)
            unique.append((text, meta, score))

    candidate_texts = [u[0] for u in unique[: max(top_k * 2, top_k)]]

    # STEP 5 → RERANKING WITH SCORES
    if use_rerank:
        reranked_items = rerank(search_query, candidate_texts, top_k)

        results = []
        for item in reranked_items:
            text = item["text"]
            score = item["score"]

            # Retrieve metadata for this chunk
            meta = next((m for t, m, s in unique if t == text), {})

            results.append({
                "text": text,
                "metadata": meta,
                "section": meta.get("section"),
                "reranker_score": score   # ⭐ REAL SCORE
            })

        return results

    # STEP 6 → NO RERANK → fallback
    results = []
    for text, meta, score in unique[:top_k]:
        results.append({
            "text": text,
            "metadata": meta,
            "section": meta.get("section"),
            "bm25_or_vec_score": score,
        })
    return results
