# =============================================================
# resume_jd_rag.py (EPHEMERAL CHROMA — ALWAYS FRESH)
# Optimized for Resume–JD Skill Gap RAG
# =============================================================

import uuid
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 🔥 BEST open-source retriever model for RAG
EMBED_MODEL = "BAAI/bge-small-en-v1.5"


# -------------------------------------------------------------
# CLEAN TEXT (Improved)
# -------------------------------------------------------------
def basic_clean(text: str):
    text = text.replace("\t", " ").replace("•", " ")
    text = " ".join(text.split())  # collapse multiple spaces
    return text.strip()


# -------------------------------------------------------------
# CREATE EMBEDDINGS + STORE IN EPHEMERAL DBs
# -------------------------------------------------------------
def get_embeddings_and_store(resume_text: str, jd_text: str):
    print("\n--------------------------------")
    print("📦 Building NEW Chroma DB (ephemeral)")
    print("--------------------------------")

    resume_clean = basic_clean(resume_text)
    jd_clean = basic_clean(jd_text)

    # 🔥 OPTIMAL CHUNK SIZE FOR RESUME/JD RAG
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=250,
        chunk_overlap=50,
        separators=["\n\n", "\n", ". "]  # ❗ Removed " " to avoid fragmentation
    )

    resume_chunks = splitter.split_text(resume_clean)
    jd_chunks = splitter.split_text(jd_clean)

    print(f"🧩 Resume chunks: {len(resume_chunks)}")
    print(f"🧩 JD chunks: {len(jd_chunks)}")

    # 🔥 BGE Embeddings
    embedder = HuggingFaceEmbeddings(model_name=EMBED_MODEL)

    # 🚀 ALWAYS NEW DB (RAM ONLY — NO PERSISTENCE)
    resume_db = Chroma(
        collection_name=f"resume_{uuid.uuid4()}",
        embedding_function=embedder,
        persist_directory=None
    )

    jd_db = Chroma(
        collection_name=f"jd_{uuid.uuid4()}",
        embedding_function=embedder,
        persist_directory=None
    )

    # ---------------------------------------------------------
    # STORE RESUME CHUNKS
    # ---------------------------------------------------------
    if resume_chunks:
        resume_db.add_texts(
            texts=resume_chunks,
            ids=[str(uuid.uuid4()) for _ in resume_chunks],
            metadatas=[
                {"section": "resume", "chunk_id": i}
                for i in range(len(resume_chunks))
            ]
        )

    # ---------------------------------------------------------
    # STORE JD CHUNKS
    # ---------------------------------------------------------
    if jd_chunks:
        jd_db.add_texts(
            texts=jd_chunks,
            ids=[str(uuid.uuid4()) for _ in jd_chunks],
            metadatas=[
                {"section": "jd", "chunk_id": i}
                for i in range(len(jd_chunks))
            ]
        )

    print("--------------------------------")
    print("📦 Embedding storage COMPLETE")
    print("--------------------------------\n")

    return {
        "resume_chunks": len(resume_chunks),
        "jd_chunks": len(jd_chunks),
        "resume_db": resume_db,
        "jd_db": jd_db
    }
