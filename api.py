"""
Enterprise AI Data Extractor — FastAPI Backend
Exposes /scrape (JSON) and /export (CSV download) endpoints.
"""

import csv
import io
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, HttpUrl

from scraper import (
    scrape_website,
    extract_body_content,
    clean_body_content,
    split_dom_content,
)
from ai_parser import parse_with_ollama, ExtractedData

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
)

app = FastAPI(
    title="Enterprise AI Data Extractor",
    version="1.0.0",
    description="Scrape any website and extract structured data using LLMs.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------
class ScrapeRequest(BaseModel):
    url: HttpUrl
    parse_description: str


class ScrapeResponse(BaseModel):
    url: str
    parse_description: str
    data: ExtractedData


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.post("/scrape", response_model=ScrapeResponse)
async def scrape_endpoint(req: ScrapeRequest):
    """
    Scrape a web page and extract structured data via LLM.

    Returns a JSON object containing the extracted items.
    """
    try:
        html = await scrape_website(str(req.url))
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    body = extract_body_content(html)
    if not body:
        raise HTTPException(
            status_code=422,
            detail="Could not extract <body> content from the page.",
        )

    cleaned = clean_body_content(body)
    chunks = split_dom_content(cleaned)

    try:
        extracted = await parse_with_ollama(chunks, req.parse_description)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=f"AI parsing error: {exc}")

    return ScrapeResponse(
        url=str(req.url),
        parse_description=req.parse_description,
        data=extracted,
    )


@app.post("/export")
async def export_endpoint(req: ScrapeRequest):
    """
    Scrape a web page, extract data, and return a downloadable CSV file.
    """
    # Reuse the /scrape logic
    try:
        html = await scrape_website(str(req.url))
    except TimeoutError as exc:
        raise HTTPException(status_code=504, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    body = extract_body_content(html)
    if not body:
        raise HTTPException(
            status_code=422,
            detail="Could not extract <body> content from the page.",
        )

    cleaned = clean_body_content(body)
    chunks = split_dom_content(cleaned)

    try:
        extracted = await parse_with_ollama(chunks, req.parse_description)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=f"AI parsing error: {exc}")

    # Build CSV in memory
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=["name", "value", "context"])
    writer.writeheader()
    for item in extracted.items:
        writer.writerow(item.model_dump())

    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=extracted_data.csv"},
    )


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    return {"status": "ok"}
