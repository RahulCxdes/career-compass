# =============================================================
# missing_skills.py (FIXED VERSION)
# =============================================================

import json
import re
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer, util

embed_model = SentenceTransformer("BAAI/bge-base-en-v1.5")


def load_skill_dictionary(path="skills_dictionary.json"):
    with open(path, "r", encoding="utf-8") as f:
        skills = json.load(f)

    return sorted(list(set([s.lower().strip() for s in skills])))


SKILL_DICTIONARY = load_skill_dictionary()


def clean_text(text: str):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\+\#\.\- ]", " ", text)
    return text


# ============================================
# FIX 1 — Remove single-letter skills + fix multi-word detection
# ============================================
def extract_dictionary_skills(text: str):
    text = clean_text(text)
    found = []

    for skill in SKILL_DICTIONARY:

        skill_clean = skill.lower().strip()

        # ❌ Ignore single-letter skills -> fix C / R issue
        if len(skill_clean) <= 1:
            continue

        # MULTI-WORD or SYMBOL SKILLS → substring match
        if " " in skill_clean or "/" in skill_clean or "-" in skill_clean:
            if skill_clean in text:
                found.append(skill_clean)
            continue

        # SINGLE WORD SKILL → STRICT word boundary match
        esc = re.escape(skill_clean)
        pattern = r"\b" + esc + r"\b"

        if re.search(pattern, text):
            found.append(skill_clean)

    return sorted(list(set(found)))


# ============================================
# FIX 2 — Prevent false semantic matches (AWS, microservices, etc.)
# ============================================
def semantic_match(resume_skills, jd_skills, threshold=0.75):
    if not resume_skills or not jd_skills:
        return []

    r_emb = embed_model.encode(resume_skills, convert_to_tensor=True)
    j_emb = embed_model.encode(jd_skills, convert_to_tensor=True)

    resume_text = " ".join(resume_skills)

    matched = []

    for i, jd_s in enumerate(jd_skills):

        # HARD RULE — Resume must contain at least one word from JD skill
        # This blocks AWS, microservices, microservices architecture
        words = jd_s.split()
        if not any(w in resume_text for w in words):
            continue

        # Semantic similarity check
        score = util.cos_sim(j_emb[i], r_emb)[0].max().item()

        if score >= threshold:
            matched.append(jd_s)

    return matched


def bm25_match(resume_skills, jd_skills):
    if not resume_skills or not jd_skills:
        return []

    bm25 = BM25Okapi([resume_skills])
    scores = bm25.get_scores(jd_skills)

    return [
        jd_skills[i]
        for i, sc in enumerate(scores)
        if sc > 0
    ]


def extract_resume_jd_skills(resume_text: str, jd_text: str):

    resume_skills = extract_dictionary_skills(resume_text)
    jd_skills = extract_dictionary_skills(jd_text)

    bm25_m = bm25_match(resume_skills, jd_skills)
    sem_m = semantic_match(resume_skills, jd_skills)

    matched = sorted(list(set(bm25_m + sem_m)))

    missing = sorted([s for s in jd_skills if s not in matched])
    extra = sorted([s for s in resume_skills if s not in matched])

    return matched, missing, extra
