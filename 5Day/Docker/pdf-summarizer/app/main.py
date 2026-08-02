"""PDF Summarizer — minimal Claude-powered FastAPI app for the Docker demo."""

import base64
import os

import anthropic
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-5")
MAX_PDF_BYTES = 32 * 1024 * 1024  # Claude's per-request PDF limit

app = FastAPI(title="PDF Summarizer")

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def get_client() -> anthropic.Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="ANTHROPIC_API_KEY is not set on the server.",
        )
    return anthropic.Anthropic(api_key=api_key)


@app.get("/")
def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/api/health")
def health():
    return {"status": "ok", "model": MODEL}


@app.post("/api/summarize")
async def summarize(file: UploadFile = File(...)):
    if file.content_type != "application/pdf" and not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a PDF file.")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(pdf_bytes) > MAX_PDF_BYTES:
        raise HTTPException(status_code=400, detail="PDF exceeds the 32MB limit.")

    pdf_b64 = base64.standard_b64encode(pdf_bytes).decode("utf-8")

    client = get_client()
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1500,
            output_config={"effort": "medium"},
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                "data": pdf_b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": (
                                "Summarize this PDF for someone who hasn't read it. "
                                "Give a short overview, then 3-6 key bullet points. "
                                "Keep it concise and skip preamble."
                            ),
                        },
                    ],
                }
            ],
        )
    except anthropic.APIStatusError as e:
        raise HTTPException(status_code=502, detail=f"Claude API error: {e.message}")
    except anthropic.APIConnectionError:
        raise HTTPException(status_code=502, detail="Could not reach the Claude API.")

    if response.stop_reason == "refusal":
        raise HTTPException(status_code=422, detail="Claude declined to summarize this document.")

    summary = "".join(block.text for block in response.content if block.type == "text")
    return {"filename": file.filename, "summary": summary, "model": MODEL}
