"""
FULL RAG-ENABLED ANALYZE PIPELINE
- Retrieves top-k chunks from Resume & JD
- Sends them + skills + scores + summaries to LLM
- Produces deep, grounded analysis
"""

import os
import json
from typing import Dict, Any, List

from langchain_chroma import Chroma
from groq import Groq

from similarity_score import compute_similarity_score 
from missing_skills import extract_resume_jd_skills


# -----------------------------------------------------------
# GET GROQ CLIENT
# -----------------------------------------------------------
def get_groq_client() -> Groq:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("❌ GROQ_API_KEY not set.")
    return Groq(api_key=api_key)


# -----------------------------------------------------------
# SIMPLE SKILL MATCHING
# -----------------------------------------------------------
def analyze_skills(resume_text: str, jd_text: str):
    matched, missing, extra = extract_resume_jd_skills(resume_text, jd_text)
    return {
        "matched_skills": matched,
        "missing_skills": missing,
        "extra_skills": extra
    }


# -----------------------------------------------------------
# RAG RETRIEVAL (NEW)
# -----------------------------------------------------------
def retrieve_top_chunks(db: Chroma, query: str, k: int = 5) -> List[str]:
    try:
        docs = db.similarity_search(query, k=k)
        return [d.page_content for d in docs]
    except Exception:
        return []


# -----------------------------------------------------------
# LLM CALL WITH RAG CONTEXT
# -----------------------------------------------------------
def generate_gap_analysis_with_llm(
    *,
    similarity: float,
    match_score: float,
    resume_chunks: List[str],
    jd_chunks: List[str],
    model_name="llama-3.1-8b-instant"
) -> str:

    client = get_groq_client()

    payload = {
        "similarity_score": similarity,
        "match_score_0_10": match_score,
        "resume_chunks": resume_chunks,
        "jd_chunks": jd_chunks,
    }

    prompt = f"""
You are an ATS-grade AI Job Readiness Assistant.

You will receive:
- Retrieved resume context chunks
- Retrieved job description context chunks
- Similarity/match score metadata

Use ONLY these retrieved chunks.  
Do NOT hallucinate skills or details not present in the chunks.

RAG CONTEXT:
{json.dumps(payload, indent=2, ensure_ascii=False)}

Your Task:
1. Identify which skills or requirements appear in the JD chunks but NOT in resume chunks.
2. Explain why they matter for the job.
3. Suggest ONE actionable improvement the candidate can make.
4. Keep the output simple, helpful, and in natural language.
5. DO NOT output JSON.

OUTPUT EXAMPLE:
"This role requires AWS and Docker, but your resume does not mention them.
Consider adding any cloud or DevOps-related experience.

Actionable Tip:
Highlight your Python backend project — it strongly aligns with the job requirements."
"""

    resp = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
        temperature=0.3,
    )

    return resp.choices[0].message.content.strip()



# -----------------------------------------------------------
# 🔥 MAIN ORCHESTRATOR — NOW FULL RAG
# -----------------------------------------------------------
# ===================================================================
# UPDATED: FULL GAP ANALYSIS ORCHESTRATOR (Hybrid: RAG + Dictionary)
# ===================================================================

def run_gap_analysis(resume_db: Chroma, jd_db: Chroma) -> Dict[str, Any]:

    # ------------------------------------------
    # 1. RAW TEXT (used ONLY for dictionary logic, NOT for LLM)
    # ------------------------------------------
    resume_raw = "\n".join(resume_db._collection.get()["documents"])
    jd_raw = "\n".join(jd_db._collection.get()["documents"])

    # ------------------------------------------
    # 2. SKILL MATCHING (kept exactly as before)
    # ------------------------------------------
    matched, missing, extra = extract_resume_jd_skills(resume_raw, jd_raw)
    skills = {
        "matched_skills": matched,
        "missing_skills": missing,
        "extra_skills": extra
    }

    # ------------------------------------------
    # 3. SIMILARITY SCORE + MATCH SCORE
    # ------------------------------------------
    similarity, match_score = compute_similarity_score(resume_raw, jd_raw)

    # ------------------------------------------
    # 4. RAG RETRIEVAL (Resume + JD)
    # ------------------------------------------
    resume_chunks = retrieve_top_chunks(
        resume_db,
        "Important strengths, projects, skills from resume",
        k=5
    )
    jd_chunks = retrieve_top_chunks(
        jd_db,
        "Key job requirements, required skills, responsibilities",
        k=5
    )

    if not resume_chunks:
        resume_chunks = ["Resume content missing."]
    if not jd_chunks:
        jd_chunks = ["JD content missing."]

    # ------------------------------------------
    # 5. LLM GAP ANALYSIS (NO dictionary skills passed!)
    # ------------------------------------------
    llm_output = generate_gap_analysis_with_llm(
        similarity=similarity,
        match_score=match_score,
        resume_chunks=resume_chunks,
        jd_chunks=jd_chunks,
    )

    # ------------------------------------------
    # 6. FINAL RESPONSE RETURNED TO FRONTEND
    # ------------------------------------------
    return {
        "similarity_score": similarity,
        "match_score_0_10": match_score,
        "skills": skills,  # original skill dictionary results (not sent to LLM)
        "resume_retrieved_chunks": resume_chunks,
        "jd_retrieved_chunks": jd_chunks,
        "llm_analysis": llm_output,  # human-readable RAG output
    }
