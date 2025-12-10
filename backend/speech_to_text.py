# speech_to_text.py
from fastapi import APIRouter, UploadFile, File
from groq import Groq
import os

router = APIRouter()

def get_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GROQ_API_KEY for speech-to-text")
    return Groq(api_key=api_key)

@router.post("/speech-to-text")
async def speech_to_text(audio: UploadFile = File(...)):
    """
    Converts audio (wav/mp3/webm) to text using Groq Whisper.
    DOES NOT change any chatbot logic.
    """

    client = get_client()

    resp = client.audio.transcriptions.create(
        model="whisper-large-v3",
        file=(audio.filename, await audio.read())
    )

    return {"text": resp.text}
