from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import JSONResponse
from typing import Optional
from urllib.parse import urlparse

app = FastAPI(title="Audio Analysis API")


def _is_valid_url(value: str) -> bool:
    try:
        result = urlparse(value)
        return result.scheme in ("http", "https") and bool(result.netloc)
    except ValueError:
        return False


@app.post("/analyze")
async def analyze(
    file: Optional[UploadFile] = File(default=None),
    url: Optional[str] = Form(default=None),
):
    if file is not None:
        return {"source": "file", "filename": file.filename}

    if url is not None:
        if not _is_valid_url(url):
            return JSONResponse(
                status_code=422,
                content={"error": "The provided URL is not valid."},
            )
        return {"source": "url", "url": url}

    return JSONResponse(
        status_code=400,
        content={"error": "Please provide an audio file or a YouTube URL."},
    )
