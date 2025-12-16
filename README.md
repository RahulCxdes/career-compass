# Career Compass

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

---

## 🏗️ System Architecture

<img src="docs/rag_flow.diagram().png" alt="Career Compass RAG Architecture" width="400"/>

---

## 🛠️ Tech Stack

### Backend
- **FastAPI** – Modern, high-performance Python web framework  
- **LangChain** – RAG pipeline orchestration  
- **ChromaDB** – Vector database for embedding storage  
- **HuggingFace Sentence Transformers** – Embeddings (`BAAI/bge-base-en-v1.5`)  
- **Groq API** – LLM inference (`Llama 3.1`)  
- **PyMuPDF (fitz)** – PDF text extraction  
- **Rank-BM25** – Keyword-based retrieval  
- **Cross-Encoder (MS MARCO MiniLM)** – Reranking for hybrid search  

### Frontend
- **React** – UI framework  
- **React Router** – Client-side navigation  
- **Web Speech API** – Voice input and text-to-speech  

---

## 📦 Setup & Installation

### Prerequisites
- **Python 3.9+**
- **Node.js 16+**
- **Groq API Key**

---

## 1️⃣ Clone the Repository

```bash
git clone <your-repo-url>
cd career-compass
```

---

## 2️⃣ Backend Setup

### Create Virtual Environment (Recommended)

```bash
python -m venv venv
```

### Activate Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**Mac/Linux:**
```bash
source venv/bin/activate
```

### Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the root or backend directory:

```env
GROQ_API_KEY=your_groq_api_key_here
```

Or export directly:

```bash
export GROQ_API_KEY="your_groq_api_key_here"
```

### Start Backend Server

```bash
uvicorn main:app --reload
```

Backend will run at: **http://localhost:8000**

---

## 3️⃣ Frontend Setup

### Navigate to Frontend

```bash
cd frontend
```

### Install Dependencies

```bash
npm install
```

### Start Frontend Server

```bash
npm start
```

Frontend will run at: **http://localhost:3000**

---

## 🚀 How to Use

### 1. Resume & JD Analysis

* Navigate to `/analyzer`
* Upload PDF or paste text
* Click **Analyze**

### 2. View Results

* Resume–JD similarity score (0–10)
* Matched, missing, and extra skills
* AI-generated gap analysis and recommendations

### 3. Career Coach Chatbot

* Open the chat drawer (💬)
* Ask questions like:
  * "How can I improve my resume?"
  * "What skills am I missing?"
  * "Suggest projects to add"
* Use voice input (🎤) for hands-free interaction

---

## 📝 Notes

* Ensure both backend and frontend servers are running simultaneously for full functionality
* Keep your Groq API key secure and never commit it to version control
* For any issues, check the console logs in both terminals

## 📧 Contact

For questions or support, please open an issue in the repository.
