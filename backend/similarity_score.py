
from sentence_transformers import SentenceTransformer, util

embed_model = SentenceTransformer("BAAI/bge-base-en-v1.5")


def compute_similarity_score(resume_text: str, jd_text: str):
    """
    Computes semantic similarity between Resume and Job Description
    using BGE-base embeddings.

    Returns:
        similarity (float)
        match_score (float)
    """

    resume_embed = embed_model.encode(resume_text, convert_to_tensor=True)
    jd_embed = embed_model.encode(jd_text, convert_to_tensor=True)

    similarity = util.cos_sim(resume_embed, jd_embed).item()

    match_score = round(similarity * 10, 2)

    return similarity, match_score
