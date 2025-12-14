
from sentence_transformers import CrossEncoder

reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

def rerank(query: str, docs: list, top_k: int = 3):
    """
    Returns TOP-K reranked docs with scores:
    [
       {"text": "...", "score": 0.91},
       {"text": "...", "score": 0.77}
    ]
    """
    if not docs:
        return []

    pairs = [[query, d] for d in docs]

    scores = reranker.predict(pairs)

    scored_docs = [
        {"text": d, "score": float(s)}
        for d, s in zip(docs, scores)
    ]

    scored_docs.sort(key=lambda x: x["score"], reverse=True)

    return scored_docs[:top_k]
