"""
FULL RAG-ENABLED ANALYZE PIPELINE
- Hybrid retrieval from Resume & JD (BM25 + embeddings + rerank)
- Section-aware (skills / experience / projects / requirements / responsibilities)
- Sends chunks + scores to LLM for gap analysis
"""

import os
import json
from typing import Dict, Any, List

from langchain_chroma import Chroma
from groq import Groq

from similarity_score import compute_similarity_score
# 🔥 removed old dictionary matcher:
# from missing_skills import extract_resume_jd_skills

from query_expansion import expand_query
from hybrid_retrieval import hybrid_search


# -----------------------------------------------------------
# GROQ CLIENT
# -----------------------------------------------------------
def get_groq_client() -> Groq:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("❌ GROQ_API_KEY not set.")
    return Groq(api_key=api_key)


# -----------------------------------------------------------
# HELPER: NORMALIZE CHUNKS
# -----------------------------------------------------------
def _ensure_chunk_dict(c: Any, default_section: str = "other") -> Dict[str, Any]:
    """
    Some retrievers return dicts with text/metadata, some just strings.
    Normalize so the rest of the pipeline can always expect a dict.
    """
    if isinstance(c, dict):
        # ensure 'section' field exists
        if "section" not in c:
            meta = c.get("metadata", {})
            c["section"] = meta.get("section", default_section)
        if "text" not in c and "page_content" in c:
            c["text"] = c["page_content"]
        return c
    else:
        # plain string → wrap
        return {
            "text": str(c),
            "section": default_section,
        }


def _normalize_chunk_list(chunks: List[Any], default_section: str) -> List[Dict[str, Any]]:
    return [_ensure_chunk_dict(c, default_section=default_section) for c in chunks]


# -----------------------------------------------------------
# WEIGHTED, SECTION-AWARE RETRIEVAL
# -----------------------------------------------------------
def _retrieve_weighted_resume_context(resume_db: Chroma) -> List[Dict[str, Any]]:
    """
    Multi-vector style retrieval for resume:
      - skills
      - experience
      - projects
      - fallback general
    """
    if resume_db is None:
        return [_ensure_chunk_dict("Resume content missing.", default_section="other")]

    collected: List[Dict[str, Any]] = []

    # 1) Skills-focused
    q_skills = expand_query(
        "Important technical and soft skills from the candidate's resume that relate to the job."
    )
    skills_raw = hybrid_search(
        search_query=q_skills,
        db=resume_db,
        top_k=3,
        bm25_k=20,
        vec_k=20,
        use_rerank=True,
        section_filter="skills",
    )
    skills_chunks = _normalize_chunk_list(skills_raw, default_section="skills")
    collected.extend(skills_chunks)

    # 2) Experience-focused
    q_exp = expand_query(
        "Most relevant work experience, responsibilities, and achievements from the candidate's resume."
    )
    exp_raw = hybrid_search(
        search_query=q_exp,
        db=resume_db,
        top_k=3,
        bm25_k=20,
        vec_k=20,
        use_rerank=True,
        section_filter="experience",
    )
    exp_chunks = _normalize_chunk_list(exp_raw, default_section="experience")
    for c in exp_chunks:
        if c not in collected:
            collected.append(c)

    # 3) Projects-focused
    q_proj = expand_query(
        "Important projects that show the candidate's impact, technologies, and outcomes."
    )
    proj_raw = hybrid_search(
        search_query=q_proj,
        db=resume_db,
        top_k=2,
        bm25_k=20,
        vec_k=20,
        use_rerank=True,
        section_filter="projects",
    )
    proj_chunks = _normalize_chunk_list(proj_raw, default_section="projects")
    for c in proj_chunks:
        if c not in collected:
            collected.append(c)

    # 4) Fallback: general resume context if still not enough
    if len(collected) < 5:
        q_general = expand_query(
            "Important strengths, skills, projects, and experience from the candidate's resume."
        )
        general_raw = hybrid_search(
            search_query=q_general,
            db=resume_db,
            top_k=5 - len(collected),
            bm25_k=20,
            vec_k=20,
            use_rerank=True,
            section_filter=None,
        )
        general_chunks = _normalize_chunk_list(general_raw, default_section="other")
        for c in general_chunks:
            if c not in collected:
                collected.append(c)

    if not collected:
        collected = [_ensure_chunk_dict("Resume content missing.", default_section="other")]

    return collected


def _retrieve_weighted_jd_context(jd_db: Chroma) -> List[Dict[str, Any]]:
    """
    Multi-vector style retrieval for JD:
      - requirements
      - responsibilities
      - fallback general
    """
    if jd_db is None:
        return [_ensure_chunk_dict("JD content missing.", default_section="other")]

    collected: List[Dict[str, Any]] = []

    # 1) Requirements-focused
    q_req = expand_query(
        "Key job requirements, required skills, and must-have qualifications from this job description."
    )
    req_raw = hybrid_search(
        search_query=q_req,
        db=jd_db,
        top_k=4,
        bm25_k=20,
        vec_k=20,
        use_rerank=True,
        section_filter="requirements",
    )
    req_chunks = _normalize_chunk_list(req_raw, default_section="requirements")
    collected.extend(req_chunks)

    # 2) Responsibilities-focused
    q_resp = expand_query(
        "Main responsibilities, day-to-day tasks, and expectations from this job description."
    )
    resp_raw = hybrid_search(
        search_query=q_resp,
        db=jd_db,
        top_k=3,
        bm25_k=20,
        vec_k=20,
        use_rerank=True,
        section_filter="responsibilities",
    )
    resp_chunks = _normalize_chunk_list(resp_raw, default_section="responsibilities")
    for c in resp_chunks:
        if c not in collected:
            collected.append(c)

    # 3) Fallback general JD context
    if len(collected) < 5:
        q_general = expand_query(
            "Overall key skills, technologies, and responsibilities described in this job description."
        )
        general_raw = hybrid_search(
            search_query=q_general,
            db=jd_db,
            top_k=5 - len(collected),
            bm25_k=20,
            vec_k=20,
            use_rerank=True,
            section_filter=None,
        )
        general_chunks = _normalize_chunk_list(general_raw, default_section="other")
        for c in general_chunks:
            if c not in collected:
                collected.append(c)

    if not collected:
        collected = [_ensure_chunk_dict("JD content missing.", default_section="other")]

    return collected


# -----------------------------------------------------------
# LLM-BASED SKILL EXTRACTION (RAG-GROUNDED)
# -----------------------------------------------------------
def extract_skills_with_llm(
    resume_chunks: List[Dict[str, Any]],
    jd_chunks: List[Dict[str, Any]],
    model_name: str = "llama-3.1-8b-instant",
) -> Dict[str, List[str]]:
    """
    Replaces the old dictionary-based skill matcher.

    Uses ONLY the retrieved resume + JD chunks and asks the LLM to:
      - find skills in JD
      - find skills in Resume
      - compute matched / missing / extra

    Returns:
      {
        "matched_skills": [...],
        "missing_skills": [...],
        "extra_skills": [...]
      }
    """

    client = get_groq_client()

    prompt = f"""
You are an ATS-grade Skill Extraction Assistant.

You will receive:
- RESUME_CONTEXT_CHUNKS: text snippets from a candidate's resume
- JD_CONTEXT_CHUNKS: text snippets from a job description

Your job is to:
1. Identify individual SKILL NAMES from each side (technologies, tools, frameworks, libraries, languages, cloud platforms, etc.).
2. Normalize them into short, lowercase names (e.g. "python", "react", "docker", "aws").
3. Compute three sets:
   - "matched_skills": skills clearly present in BOTH resume and JD.
   - "missing_skills": skills required in JD but NOT clearly present in resume.
   - "extra_skills": skills present in resume but NOT mentioned in JD.

VERY IMPORTANT RULES:
- Only include real skills (not soft phrases like "hardworking").
- Keep each skill as a SHORT STRING (no sentences).
- If unsure about a skill, leave it out.
- If nothing is found for a set, return an empty list for that set.

RESUME_CONTEXT_CHUNKS:
{json.dumps(resume_chunks, indent=2, ensure_ascii=False)}

JD_CONTEXT_CHUNKS:
{json.dumps(jd_chunks, indent=2, ensure_ascii=False)}

Now respond with ONLY valid JSON in this exact format:

{{
  "matched_skills": ["skill1", "skill2"],
  "missing_skills": ["skill3"],
  "extra_skills": ["skill4"]
}}
"""

    resp = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=400,
        temperature=0.1,
    )

    raw = resp.choices[0].message.content.strip()

    # Try to robustly parse JSON
    try:
        # Sometimes LLM may wrap in ```json ... ```
        if raw.startswith("```"):
            raw = raw.strip("`")
            # remove possible "json" label
            if raw.lower().startswith("json"):
                raw = raw[4:].strip()
        data = json.loads(raw)
    except Exception:
        # Fallback: safe empty structure
        data = {}

    matched = data.get("matched_skills", []) or []
    missing = data.get("missing_skills", []) or []
    extra = data.get("extra_skills", []) or []

    # Ensure they are lists of strings
    matched = [str(s).strip() for s in matched if str(s).strip()]
    missing = [str(s).strip() for s in missing if str(s).strip()]
    extra = [str(s).strip() for s in extra if str(s).strip()]

    return {
        "matched_skills": matched,
        "missing_skills": missing,
        "extra_skills": extra,
    }


# -----------------------------------------------------------
# LLM GAP ANALYSIS (RAG-GROUNDED)
# -----------------------------------------------------------
def generate_gap_analysis_with_llm(
    *,
    similarity: float,
    match_score: float,
    resume_chunks: List[Dict[str, Any]],
    jd_chunks: List[Dict[str, Any]],
    model_name: str = "llama-3.1-8b-instant",
) -> str:

    client = get_groq_client()

    prompt = f"""
You are an ATS-grade AI Job Readiness Assistant.

You will receive:
- RESUME_CONTEXT: chunks from the candidate's resume
- JD_CONTEXT: chunks from the job description
- Similarity and match score metadata

Use ONLY the given context. Do NOT hallucinate skills or experience
that are not clearly present in the provided chunks.

RESUME_CONTEXT:
{json.dumps(resume_chunks, indent=2, ensure_ascii=False)}

JD_CONTEXT:
{json.dumps(jd_chunks, indent=2, ensure_ascii=False)}

METADATA:
{json.dumps({"similarity_score": similarity, "match_score_0_10": match_score}, indent=2, ensure_ascii=False)}

Your Task:
1. Identify which skills or requirements in the JD_CONTEXT are NOT clearly present in RESUME_CONTEXT.
2. Briefly explain why those missing skills/requirements matter for this role.
3. Highlight the candidate's strongest matching points from the resume.
4. Suggest 2–3 concrete, actionable improvements (skills to learn, projects to add, how to rewrite resume).
5. Keep the output in clear paragraphs and bullet points. Do NOT output JSON.
"""

    resp = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=700,
        temperature=0.3,
    )

    return resp.choices[0].message.content.strip()


# ===================================================================
# MAIN ORCHESTRATOR
# ===================================================================
def run_gap_analysis(resume_db: Chroma, jd_db: Chroma) -> Dict[str, Any]:
    # 1. RAW TEXT (for similarity score only)
    resume_docs = resume_db._collection.get().get("documents", []) if resume_db is not None else []
    jd_docs = jd_db._collection.get().get("documents", []) if jd_db is not None else []

    resume_raw = "\n".join(resume_docs)
    jd_raw = "\n".join(jd_docs)

    # 2. Similarity + Match Score (unchanged)
    similarity, match_score = compute_similarity_score(resume_raw, jd_raw)

    # 3. Section-aware, hybrid RAG retrieval (unchanged)
    resume_chunks = _retrieve_weighted_resume_context(resume_db)
    jd_chunks = _retrieve_weighted_jd_context(jd_db)

    # 4. NEW: LLM-based skill extraction using retrieved chunks
    skills = extract_skills_with_llm(resume_chunks, jd_chunks)

    # 5. LLM gap analysis (RAG-grounded, unchanged)
    llm_output = generate_gap_analysis_with_llm(
        similarity=similarity,
        match_score=match_score,
        resume_chunks=resume_chunks,
        jd_chunks=jd_chunks,
    )

    # Debug prints – still safe, always dicts
    print("\n===== RESUME RETRIEVED CHUNKS =====")
    for idx, c in enumerate(resume_chunks, 1):
        text = c.get("text", "")[:150]
        section = c.get("section", "unknown")
        print(f"[{idx}] Section: {section} | Text: {text}")

    print("\n===== JD RETRIEVED CHUNKS =====")
    for idx, c in enumerate(jd_chunks, 1):
        text = c.get("text", "")[:150]
        section = c.get("section", "unknown")
        print(f"[{idx}] Section: {section} | Text: {text}")

    # 6. Final structured result  ✅ same shape as before
    return {
        "similarity_score": similarity,
        "match_score_0_10": match_score,
        "skills": skills,
        "resume_retrieved_chunks": resume_chunks,
        "jd_retrieved_chunks": jd_chunks,
        "llm_analysis": llm_output,
    }
