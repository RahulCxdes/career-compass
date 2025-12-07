# reranker.py
from sentence_transformers import CrossEncoder

# Free, fast, strong reranker
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

    # Create pairs for scoring
    pairs = [[query, d] for d in docs]

    # Predict relevance scores
    scores = reranker.predict(pairs)

    # Attach the score to the corresponding document
    scored_docs = [
        {"text": d, "score": float(s)}
        for d, s in zip(docs, scores)
    ]

    # Sort descending by score
    scored_docs.sort(key=lambda x: x["score"], reverse=True)

    # Return top-k
    return scored_docs[:top_k]
