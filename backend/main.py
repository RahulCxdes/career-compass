from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import fitz  
import re   
from resume_jd_rag import get_embeddings_and_store  
from gap_analysis_llm import run_gap_analysis   
       
from fastapi import FastAPI
from chat_endpoint import router as chat_router
from memory_db import resume_db as mem_resume_db, jd_db as mem_jd_db
from speech_to_text import router as stt_router



app = FastAPI()
app.include_router(stt_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def extract_pdf_text(file: UploadFile):
    content = file.file.read()
    pdf = fitz.open(stream=content, filetype="pdf")
    text = ""

    for page in pdf:
        text += page.get_text("text") + "\n" 


    text = text.replace("C++", "cpp").replace("c++", "cpp")

 
    text = re.sub(r"(?<=\s)[a-zA-Z](?=\s)", " ", text)


    cleaned_lines = []
    for line in text.split("\n"):
        cleaned_lines.append(" ".join(line.split())) 

    cleaned_text = "\n".join(cleaned_lines).strip()
    return cleaned_text

@app.post("/analyze")
async def analyze(
    resume_file: UploadFile = File(None),
    resume_text: str = Form(""),
    jd_file: UploadFile = File(None),
    jd_text: str = Form("")
):
    print("\n🚀 /analyze CALLED")

    if resume_file:
        resume = extract_pdf_text(resume_file)
        print("📄 Using RESUME PDF input...")
    else:
        resume = resume_text or ""
        print("📄 Using RESUME TEXT input...")

    if jd_file:
        jd = extract_pdf_text(jd_file)
        print("📄 Using JD PDF input...")
    else:
        jd = jd_text or ""
        print("📄 Using JD TEXT input...")

    print("📄 Resume length:", len(resume))
    print("📄 JD length:", len(jd))

    store_info = get_embeddings_and_store(resume, jd)

    resume_db = store_info["resume_db"]
    jd_db = store_info["jd_db"]

    result = run_gap_analysis(resume_db, jd_db)

    import memory_db
    memory_db.resume_db = resume_db
    memory_db.jd_db = jd_db
    memory_db.similarity_score = result["similarity_score"]
    memory_db.match_score = result["match_score_0_10"]
    memory_db.resume_text = resume_text
    memory_db.jd_text = jd_text

    return JSONResponse(result)
