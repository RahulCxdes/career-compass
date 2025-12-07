# =============================================================
# resume_jd_rag.py (Final Updated Version)
# Section-Aware RAG for Resume/JD with:
# - Strict Experience Detection
# - Achievement Section
# - Clean Project & Skill Detection
# =============================================================

import uuid
import re
from typing import Dict, List, Tuple

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter


EMBED_MODEL = "BAAI/bge-small-en-v1.5"


# -------------------------------------------------------------
# BASIC CLEANING (preserve newlines)
# -------------------------------------------------------------
def basic_clean(text: str) -> str:
    text = text.replace("\t", " ").replace("•", " ")
    lines = [" ".join(line.split()) for line in text.split("\n")]
    return "\n".join(lines).strip()


# -------------------------------------------------------------
# FIXED SECTION HEADINGS
# -------------------------------------------------------------
SECTION_KEYWORDS = {
    "summary": ["summary", "professional summary", "profile", "objective"],
    "skills": ["skills", "technical skills", "key skills"],
    "projects": ["projects", "project"],
    "education": ["education", "academic background"],
}


# -------------------------------------------------------------
# NORMALIZE HEADING
# -------------------------------------------------------------
def _normalize_heading(line: str) -> str:
    return re.sub(r"[^a-zA-Z ]", " ", line.lower()).strip()


# -------------------------------------------------------------
# AUTO-DETECT PROJECTS USING "|" PATTERN
# -------------------------------------------------------------
def _looks_like_project(line: str) -> bool:
    # Example: "News Summarization | Python, NLTK"
    if "|" in line and len(line.split("|")[0].strip()) > 3:
        return True
    return False


# -------------------------------------------------------------
# STRICT EXPERIENCE DETECTOR
# -------------------------------------------------------------
def _is_experience_line(text: str) -> bool:
    text_l = text.lower()

    strong_exp_keywords = [
        "experience", "work experience",
        "employment", "internship", "intern",
        "worked at", "role", "responsibilities"
    ]

    # Only assign to experience section if HIGH confidence keyword is present
    return any(k in text_l for k in strong_exp_keywords)


# -------------------------------------------------------------
# ACHIEVEMENTS DETECTOR
# -------------------------------------------------------------
def _is_achievement_line(text: str) -> bool:
    text_l = text.lower()

    achievement_keywords = [
        "award", "achievement", "certificate", "certification",
        "certified", "nptel", "honored", "recognition", "prize",
        "dr. a.p.j", "kalam"
    ]

    return any(k in text_l for k in achievement_keywords)


# -------------------------------------------------------------
# DETECT SECTION FROM HEADING
# -------------------------------------------------------------
def _detect_section_from_line(line: str) -> str:
    norm = _normalize_heading(line)
    for section, keywords in SECTION_KEYWORDS.items():
        for kw in keywords:
            if kw in norm:
                return section
    return ""


# -------------------------------------------------------------
# MAIN SECTION SPLITTER (FINAL FIXED VERSION)
# -------------------------------------------------------------
def split_into_sections(raw_text: str, default_section="other") -> Dict[str, str]:
    lines = raw_text.split("\n")
    sections: Dict[str, List[str]] = {}
    current_section = default_section

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # 1️⃣ Auto-detect project entries
        if _looks_like_project(stripped):
            current_section = "projects"
            sections.setdefault("projects", []).append(stripped)
            continue

        # 2️⃣ Strict experience detection
        if _is_experience_line(stripped):
            current_section = "experience"
            sections.setdefault("experience", [])
            continue

        # 3️⃣ Achievement detection
        if _is_achievement_line(stripped):
            current_section = "achievements"
            sections.setdefault("achievements", []).append(stripped)
            continue

        # 4️⃣ Heading detection for: summary, skills, projects, education
        detected = _detect_section_from_line(stripped)

        # Prevent accidental experience classification
        if detected == "experience" and not _is_experience_line(stripped):
            detected = None

        if detected:
            current_section = detected
            sections.setdefault(current_section, [])
            continue

        # 5️⃣ Prevent accidental experience content fall-in
        if current_section == "experience" and not _is_experience_line(stripped):
            current_section = "other"

        # 6️⃣ Add content safely
        sections.setdefault(current_section, []).append(stripped)

    return {sec: "\n".join(content).strip() for sec, content in sections.items()}


# -------------------------------------------------------------
# CHUNKING (Avoid patchy chunks)
# -------------------------------------------------------------
def chunk_section_text(section_name: str, text: str) -> List[str]:
    if not text.strip():
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=280,
        chunk_overlap=40,
        separators=["\n\n", "\n", ". "],
    )

    return splitter.split_text(text)


# -------------------------------------------------------------
# EMBEDDINGS + TEMP CHROMA DB
# -------------------------------------------------------------
def get_embeddings_and_store(resume_text: str, jd_text: str):
    print("\n--------------------------------")
    print("📦 Building NEW Chroma DB (optimized with Achievements + strict Experience)")
    print("--------------------------------")

    resume_clean = basic_clean(resume_text)
    jd_clean = basic_clean(jd_text)

    # 1) Split into sections
    resume_sections = split_into_sections(resume_clean)
    jd_sections = split_into_sections(jd_clean)

    resume_chunks_with_meta = []
    jd_chunks_with_meta = []

    # 2) Chunk per section
    for section_name, block in resume_sections.items():
        chunks = chunk_section_text(section_name, block)
        for i, ch in enumerate(chunks):
            resume_chunks_with_meta.append(
                (ch, {"doc_type": "resume", "section": section_name, "chunk_id": i})
            )

    for section_name, block in jd_sections.items():
        chunks = chunk_section_text(section_name, block)
        for i, ch in enumerate(chunks):
            jd_chunks_with_meta.append(
                (ch, {"doc_type": "jd", "section": section_name, "chunk_id": i})
            )

    print(f"🧩 Resume chunks: {len(resume_chunks_with_meta)}")
    print(f"🧩 JD chunks: {len(jd_chunks_with_meta)}")

    # 3) Create DBs
    embedder = HuggingFaceEmbeddings(model_name=EMBED_MODEL)

    resume_db = Chroma(
        collection_name=f"resume_{uuid.uuid4()}",
        embedding_function=embedder,
        persist_directory=None,
    )

    jd_db = Chroma(
        collection_name=f"jd_{uuid.uuid4()}",
        embedding_function=embedder,
        persist_directory=None,
    )

    # 4) Store with metadata
    if resume_chunks_with_meta:
        resume_db.add_texts(
            texts=[t for t, _ in resume_chunks_with_meta],
            ids=[str(uuid.uuid4()) for _ in resume_chunks_with_meta],
            metadatas=[m for _, m in resume_chunks_with_meta],
        )

    if jd_chunks_with_meta:
        jd_db.add_texts(
            texts=[t for t, _ in jd_chunks_with_meta],
            ids=[str(uuid.uuid4()) for _ in jd_chunks_with_meta],
            metadatas=[m for _, m in jd_chunks_with_meta],
        )

    print("--------------------------------")
    print("📦 Embedding storage COMPLETE")
    print("--------------------------------\n")

    return {
        "resume_chunks": len(resume_chunks_with_meta),
        "jd_chunks": len(jd_chunks_with_meta),
        "resume_db": resume_db,
        "jd_db": jd_db,
    }
