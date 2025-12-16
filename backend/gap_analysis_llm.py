

import os
import json
from typing import Dict, Any, List
import re
from langchain_chroma import Chroma
from groq import Groq

from similarity_score import compute_similarity_score
from query_expansion import expand_query
from hybrid_retrieval import hybrid_search



def get_groq_client() -> Groq:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("❌ GROQ_API_KEY not set.")
    return Groq(api_key=api_key)



def _ensure_chunk_dict(c: Any, default_section: str = "other") -> Dict[str, Any]:
    if isinstance(c, dict):
        if "section" not in c:
            meta = c.get("metadata", {})
            c["section"] = meta.get("section", default_section)
        if "text" not in c and "page_content" in c:
            c["text"] = c["page_content"]
        return c
    else:
        return {"text": str(c), "section": default_section}


def _normalize_chunk_list(chunks: List[Any], default_section: str) -> List[Dict[str, Any]]:
    return [_ensure_chunk_dict(c, default_section) for c in chunks]



def _retrieve_weighted_resume_context(resume_db: Chroma) -> List[Dict[str, Any]]:
    if resume_db is None:
        return [_ensure_chunk_dict("Resume missing.", "other")]

    collected = []


    skills_raw = hybrid_search(
        search_query=expand_query("technical skills from resume"),
        db=resume_db,
        top_k=3,
        bm25_k=20,
        vec_k=20,
        use_rerank=True,
        section_filter="skills",
    )
    collected.extend(_normalize_chunk_list(skills_raw, "skills"))


    exp_raw = hybrid_search(
        search_query=expand_query("work experience achievements"),
        db=resume_db,
        top_k=3,
        bm25_k=20,
        vec_k=20,
        use_rerank=True,
        section_filter="experience",
    )
    for c in _normalize_chunk_list(exp_raw, "experience"):
        if c not in collected:
            collected.append(c)


    proj_raw = hybrid_search(
        search_query=expand_query("important projects"),
        db=resume_db,
        top_k=2,
        bm25_k=20,
        vec_k=20,
        use_rerank=True,
        section_filter="projects",
    )
    for c in _normalize_chunk_list(proj_raw, "projects"):
        if c not in collected:
            collected.append(c)

    return collected

def _retrieve_weighted_jd_context(jd_db: Chroma) -> List[Dict[str, Any]]:
    if jd_db is None:
        return [_ensure_chunk_dict("JD missing.", "other")]

    collected = []

    req_raw = hybrid_search(
        search_query=expand_query("required skills job requirements"),
        db=jd_db,
        top_k=4,
        bm25_k=20,
        vec_k=20,
        use_rerank=True,
        section_filter="requirements",
    )
    collected.extend(_normalize_chunk_list(req_raw, "requirements"))

    resp_raw = hybrid_search(
        search_query=expand_query("responsibilities tasks"),
        db=jd_db,
        top_k=3,
        bm25_k=20,
        vec_k=20,
        use_rerank=True,
        section_filter="responsibilities",
    )
    for c in _normalize_chunk_list(resp_raw, "responsibilities"):
        if c not in collected:
            collected.append(c)


    if len(collected) < 2:
        gen_raw = hybrid_search(
            search_query=expand_query("skills technologies job description"),
            db=jd_db,
            top_k=2,
            bm25_k=20,
            vec_k=20,
            use_rerank=True,
        )
        for c in _normalize_chunk_list(gen_raw, "other"):
            if c not in collected:
                collected.append(c)

    return collected

def get_only_skill_section_text(chunks: List[Dict[str, Any]]) -> str:
    text_blocks = []
    for c in chunks:
        if c.get("section") == "skills":
            text_blocks.append(c.get("text", ""))
    return "\n".join(text_blocks).strip()



def extract_skill_lists(resume_chunks, jd_chunks):

    def get_skill_text(chunks):
        for c in chunks:
            if c.get("section") == "skills":
                return c.get("text", "")
        return ""

    resume_skill_text = get_skill_text(resume_chunks)
    jd_skill_text = get_skill_text(jd_chunks)

    def to_list(text):
        if not text:
            return []
        parts = re.split(r"[,\n]+", text)
        return [p.strip() for p in parts if p.strip()]

    resume_skill_list = to_list(resume_skill_text)
    jd_skill_list = to_list(jd_skill_text)


    print("\n===== RESUME SKILL LIST =====")
    print(resume_skill_list)

    print("\n===== JD SKILL LIST =====")
    print(jd_skill_list)


    return {
        "resume_skill_list": resume_skill_list,
        "jd_skill_list": jd_skill_list
    }


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
4. Suggest 2-3 concrete, actionable improvements (skills to learn, projects to add, how to rewrite resume).
5. Keep the output in clear paragraphs and bullet points. Do NOT output JSON.
"""

    resp = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=700,
        temperature=0.3,
    )

    return resp.choices[0].message.content.strip()



def compare_skill_lists_pure(resume_skill_list, jd_skill_list):


    def normalize(s: str):
        s = s.strip().lower()

        if s.startswith("-"):
            s = s[1:].strip()

        if ":" in s:
            prefix = s.split(":")[0]
            if any(x in prefix for x in ["programming", "framework", "library"]):
                s = s.split(":", 1)[1].strip()

        if s in ["preferred", "preferred:"]:
            return ""

        return s

    resume_clean = {normalize(s) for s in resume_skill_list if normalize(s)}
    jd_clean = {normalize(s) for s in jd_skill_list if normalize(s)}

    matched = sorted(list(resume_clean & jd_clean))
    missing = sorted(list(jd_clean - resume_clean))
    extra = sorted(list(resume_clean - jd_clean))

    return {
        "matched_skills": matched,
        "missing_skills": missing,
        "extra_skills": extra
    }


def run_gap_analysis(resume_db: Chroma, jd_db: Chroma) -> Dict[str, Any]:

    resume_docs = resume_db._collection.get().get("documents", []) if resume_db else []
    jd_docs = jd_db._collection.get().get("documents", []) if jd_db else []

    resume_raw = "\n".join(resume_docs)
    jd_raw = "\n".join(jd_docs)

    similarity, match_score = compute_similarity_score(resume_raw, jd_raw)

    resume_chunks = _retrieve_weighted_resume_context(resume_db)
    jd_chunks = _retrieve_weighted_jd_context(jd_db)

    llm_output = generate_gap_analysis_with_llm(
        similarity=similarity,
        match_score=match_score,
        resume_chunks=resume_chunks,
        jd_chunks=jd_chunks,
    )

    skill_lists = extract_skill_lists(resume_chunks, jd_chunks)

    skills = compare_skill_lists_pure(
        skill_lists["resume_skill_list"],
        skill_lists["jd_skill_list"]
)


    return {
        "similarity_score": similarity,
        "match_score_0_10": match_score,
        "skills": skills,
        "resume_retrieved_chunks": resume_chunks,
        "jd_retrieved_chunks": jd_chunks,
        "llm_analysis": llm_output,
    }
