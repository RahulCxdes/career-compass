## 📌 Project Overview

**Career Compass** is an AI-powered career assistant built using a **Retrieval-Augmented Generation (RAG)** architecture to analyze resumes against job descriptions with high precision.

The system implements **section-aware document chunking**, where resumes and JDs are intelligently split into semantic sections such as **skills, experience, projects, and requirements**. These chunks are embedded and stored separately to preserve contextual relevance.

### 🔍 Retrieval Strategy

The application uses a **hybrid search strategy** that combines:

- **BM25 keyword-based retrieval** for exact skill and term matching  
- **Dense vector similarity search (ChromaDB + BGE embeddings)** using **cosine similarity** for deeper semantic understanding  

To further improve retrieval accuracy, the system applies **LLM-based query expansion**, rewriting user inputs into explicit, search-optimized queries, and **intent detection**, which classifies whether a query targets the **resume**, the **job description**, or **both**. This ensures that retrieval is focused on the most relevant document source.

On top of the retrieved candidates, a **cross-encoder reranker (MS MARCO MiniLM)** is applied to re-score and reorder results, ensuring that only the most contextually relevant chunks are passed to the LLM.

### 🧠 Analysis & Output

The final retrieved context is then used to:

- Compute **semantic similarity scores** between the resume and job description using **cosine similarity**
- Identify **matched, missing, and extra skills**
- Generate **actionable, non-hallucinated AI recommendations** using a large language model, strictly grounded in the retrieved content

## 🏗️ System Architecture

![Career Compass RAG Architecture](./docs/architecture.png)
