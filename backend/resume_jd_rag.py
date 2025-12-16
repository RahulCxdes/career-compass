

import uuid
import re
from typing import Dict, List, Tuple

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter


EMBED_MODEL = "BAAI/bge-small-en-v1.5"

def basic_clean(text: str) -> str:
    text = text.replace("\t", " ").replace("•", " ")
    lines = [" ".join(line.split()) for line in text.split("\n")]
    return "\n".join(lines).strip()


SECTION_KEYWORDS = {
    "summary": ["summary", "professional summary", "profile", "objective"],
    "skills": ["skills", "technical skills", "key skills"],
    "projects": ["projects", "project"],
    "education": ["education", "academic background"],
}

def _normalize_heading(line: str) -> str:
    return re.sub(r"[^a-zA-Z ]", " ", line.lower()).strip()


def _looks_like_project(line: str) -> bool:

    if "|" in line and len(line.split("|")[0].strip()) > 3:
        return True
    return False

def _is_experience_line(text: str) -> bool:
    text_l = text.lower()

    strong_exp_keywords = [
        "experience", "work experience",
        "employment", "internship", "intern",
        "worked at", "role", "responsibilities"
    ]


    return any(k in text_l for k in strong_exp_keywords)


def _is_achievement_line(text: str) -> bool:
    text_l = text.lower()

    achievement_keywords = [
        "award", "achievement", "certificate", "certification",
        "certified", "nptel", "honored", "recognition", "prize",
        "dr. a.p.j", "kalam"
    ]

    return any(k in text_l for k in achievement_keywords)

def _detect_section_from_line(line: str) -> str:
    norm = _normalize_heading(line)
    for section, keywords in SECTION_KEYWORDS.items():
        for kw in keywords:
            if kw in norm:
                return section
    return ""

def split_into_sections(raw_text: str, default_section="other") -> Dict[str, str]:
    lines = raw_text.split("\n")
    sections: Dict[str, List[str]] = {}
    current_section = default_section

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        if _looks_like_project(stripped):
            current_section = "projects"
            sections.setdefault("projects", []).append(stripped)
            continue

        if _is_experience_line(stripped):
            current_section = "experience"
            sections.setdefault("experience", [])
            continue


        if _is_achievement_line(stripped):
            current_section = "achievements"
            sections.setdefault("achievements", []).append(stripped)
            continue

        detected = _detect_section_from_line(stripped)


        if detected == "experience" and not _is_experience_line(stripped):
            detected = None

        if detected:
            current_section = detected
            sections.setdefault(current_section, [])
            continue

        if current_section == "experience" and not _is_experience_line(stripped):
            current_section = "other"

        sections.setdefault(current_section, []).append(stripped)

    return {sec: "\n".join(content).strip() for sec, content in sections.items()}


def chunk_section_text(section_name: str, text: str) -> List[str]:
    if not text.strip():
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=280,
        chunk_overlap=40,
        separators=["\n\n", "\n", ". "],
    )

    return splitter.split_text(text)


def get_embeddings_and_store(resume_text: str, jd_text: str):
   

    resume_clean = basic_clean(resume_text)
    jd_clean = basic_clean(jd_text)

    resume_sections = split_into_sections(resume_clean)
    jd_sections = split_into_sections(jd_clean)

    resume_chunks_with_meta = []
    jd_chunks_with_meta = []

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

    return {
        "resume_chunks": len(resume_chunks_with_meta),
        "jd_chunks": len(jd_chunks_with_meta),
        "resume_db": resume_db,
        "jd_db": jd_db,
    }
