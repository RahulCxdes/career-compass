# reranker.py
from sentence_transformers import CrossEncoder

# Fast and accurate reranker
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

def rerank(query: str, docs: list, top_k: int = 3):
    if not docs:
        return []

    pairs = [[query, d] for d in docs]
    scores = reranker.predict(pairs)

    scored = list(zip(docs, scores))
    scored.sort(key=lambda x: x[1], reverse=True)

    return [doc for doc, score in scored[:top_k]]
