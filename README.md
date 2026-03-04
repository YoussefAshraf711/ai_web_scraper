<div align="center">

# 🔍 Enterprise AI Data Extractor

### Turn Unstructured Web Pages into Clean, Structured JSON — Powered by LLMs

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Playwright](https://img.shields.io/badge/Playwright-2EAD33?style=for-the-badge&logo=playwright&logoColor=white)](https://playwright.dev)
[![Ollama](https://img.shields.io/badge/Ollama-000000?style=for-the-badge&logo=ollama&logoColor=white)](https://ollama.ai)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

<p align="center">
  <strong>No more brittle CSS selectors. No more broken scrapers after every site redesign.<br/>
  Just tell the AI <em>what</em> you want, and get clean JSON back.</strong>
</p>

---

[Features](#-features) •
[Architecture](#-architecture) •
[Quick Start](#-quick-start) •
[API Reference](#-api-reference) •
[Use Case](#-real-world-use-case) •
[Author](#-author)

</div>

---

## 🎯 The Problem

Traditional web scrapers are **fragile**. They depend on hardcoded CSS selectors and XPath queries that break the moment a website changes its HTML structure. Every site redesign means rewriting your scraper from scratch.

## 💡 The Solution

This tool takes a fundamentally different approach: instead of writing rigid extraction rules, you **describe what data you want in plain English**, and an LLM intelligently parses the page content — regardless of how the HTML is structured.

| Traditional Scraping | AI-Powered Extraction |
|---|---|
| ❌ Hardcoded CSS selectors | ✅ Natural language instructions |
| ❌ Breaks on HTML changes | ✅ Adapts to any page structure |
| ❌ One scraper per website | ✅ One tool for all websites |
| ❌ Manual maintenance | ✅ Zero maintenance |

---

## ✨ Features

- **🎭 Async Playwright Engine** — Headless Chromium with full JavaScript rendering, faster than Selenium
- **🛡️ Anti-Bot Evasion** — Randomized User-Agent, viewport, timezone, locale, and `navigator.webdriver` stealth override
- **🧠 LLM-Powered Parsing** — Langchain + Ollama (Llama 3.2) understands page content semantically
- **📐 Structured Output** — Pydantic-validated JSON responses, never raw text — guaranteed schema conformance
- **⚡ FastAPI Backend** — Production-ready async REST API with Swagger docs
- **📊 Streamlit Frontend** — Interactive UI for quick testing and demos
- **🔄 Retry & Validation** — Hallucination guard with retry logic on malformed LLM output
- **📥 CSV Export** — One-click download of extracted data as CSV

---

## 🏗️ Architecture

```
                    ┌──────────────────────────────────────────────────────────┐
                    │                    CLIENT LAYER                         │
                    │                                                         │
                    │   ┌──────────────┐         ┌───────────────────────┐    │
                    │   │  Streamlit   │         │   Any HTTP Client     │    │
                    │   │  Frontend    │         │   (curl / Postman)    │    │
                    │   └──────┬───────┘         └───────────┬───────────┘    │
                    └──────────┼─────────────────────────────┼────────────────┘
                               │          HTTP/REST          │
                    ┌──────────▼─────────────────────────────▼────────────────┐
                    │                   API LAYER (FastAPI)                    │
                    │                                                         │
                    │   POST /scrape ──▶ JSON    POST /export ──▶ CSV         │
                    │   GET  /health             GET  /docs                   │
                    └──────────┬─────────────────────────────┬────────────────┘
                               │                             │
                    ┌──────────▼──────────┐     ┌────────────▼───────────────┐
                    │   SCRAPING ENGINE   │     │     AI PARSING LAYER      │
                    │                     │     │                            │
                    │   Playwright        │     │   Langchain + ChatOllama   │
                    │   (async Chromium)  │────▶│   Pydantic Structured     │
                    │                     │ DOM │   Output Validation       │
                    │   • Stealth JS      │     │                            │
                    │   • Random UA       │     │   • Retry on failure       │
                    │   • Anti-detection  │     │   • Hallucination guard    │
                    └─────────────────────┘     └────────────┬───────────────┘
                                                             │
                                                ┌────────────▼───────────────┐
                                                │      Ollama (Local)        │
                                                │      Llama 3.2 Model       │
                                                └────────────────────────────┘
```

**Data Flow:**
1. Client sends a URL + extraction description to the API
2. **Scraper** launches headless Chromium with anti-bot evasion, fetches & cleans the DOM
3. Cleaned text is chunked and fed to the **AI Parser**
4. LLM extracts structured data matching the description
5. Output is validated against a **Pydantic schema** and returned as JSON or CSV

---

## 🚀 Quick Start

### Prerequisites

| Requirement | Version | Purpose |
|---|---|---|
| Python | 3.10+ | Runtime |
| [Ollama](https://ollama.ai/) | Latest | Local LLM server |
| Node.js | 16+ | Playwright browser binaries |

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/youssefashraf/Enterprise-AI-Data-Extractor.git
cd Enterprise-AI-Data-Extractor

# 2. Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install Playwright's Chromium browser
playwright install chromium

# 5. Pull the Llama 3.2 model
ollama pull llama3.2
```

### Running the Application

```bash
# Terminal 1 — Start the FastAPI backend
uvicorn api:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 — Start the Streamlit frontend
streamlit run main.py
```

| Service | URL |
|---|---|
| 🖥️ Streamlit UI | `http://localhost:8501` |
| ⚡ FastAPI Server | `http://localhost:8000` |
| 📖 Swagger Docs | `http://localhost:8000/docs` |

---

## 📡 API Reference

### `POST /scrape` — Extract Data as JSON

Scrape a web page and return AI-extracted structured data.

**Request:**
```json
{
  "url": "https://example-realestate.com/listings",
  "parse_description": "Extract property name, price, location, and number of bedrooms"
}
```

**Response:**
```json
{
  "url": "https://example-realestate.com/listings",
  "parse_description": "Extract property name, price, location, and number of bedrooms",
  "data": {
    "items": [
      {
        "name": "Price",
        "value": "$450,000",
        "context": "Modern 3BR Apartment — Downtown Cairo"
      },
      {
        "name": "Bedrooms",
        "value": "3",
        "context": "Modern 3BR Apartment — Downtown Cairo"
      },
      {
        "name": "Location",
        "value": "Downtown Cairo, Egypt",
        "context": "Modern 3BR Apartment — Downtown Cairo"
      }
    ]
  }
}
```

### `POST /export` — Download Data as CSV

Same as `/scrape`, but returns a downloadable CSV file.

```bash
curl -X POST http://localhost:8000/export \
  -H "Content-Type: application/json" \
  -d '{"url": "https://quotes.toscrape.com", "parse_description": "Extract all quotes and authors"}' \
  -o extracted_data.csv
```

### `GET /health` — Health Check

```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

### Error Responses

| Status Code | Meaning |
|---|---|
| `504` | Page load timeout — site unreachable or too slow |
| `502` | Scraping engine failure |
| `422` | Could not extract `<body>` content |
| `500` | LLM parsing error — model unavailable or invalid output |

---

## 🏠 Real-World Use Case: Real Estate Data Extraction

**Scenario:** You need to extract property listings from a real estate website into a structured database for analysis.

### The Old Way (Traditional Scraper)
```python
# Fragile — breaks when HTML changes
prices = soup.select("div.listing-card > span.price-tag")
titles = soup.select("div.listing-card > h2.property-title")
# 🔴 Site redesigns? Start over.
```

### The New Way (AI Data Extractor)
```bash
curl -X POST http://localhost:8000/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example-realestate.com/cairo-apartments",
    "parse_description": "Extract all property listings with: property name, price in USD, location/neighborhood, number of bedrooms, and square footage"
  }'
```

**Result:** Clean, structured JSON — no matter how the site's HTML is organized:

```json
{
  "data": {
    "items": [
      { "name": "Property",    "value": "Nile View Penthouse",     "context": "Zamalek, Cairo" },
      { "name": "Price",       "value": "$1,200,000",              "context": "Nile View Penthouse" },
      { "name": "Bedrooms",    "value": "4",                       "context": "Nile View Penthouse" },
      { "name": "Area",        "value": "320 sqm",                 "context": "Nile View Penthouse" },
      { "name": "Property",    "value": "Garden City Studio",      "context": "Garden City, Cairo" },
      { "name": "Price",       "value": "$85,000",                 "context": "Garden City Studio" },
      { "name": "Bedrooms",    "value": "1",                       "context": "Garden City Studio" },
      { "name": "Area",        "value": "55 sqm",                  "context": "Garden City Studio" }
    ]
  }
}
```

✅ **Site redesigns don't break anything** — the LLM understands the content semantically.

---

## 📁 Project Structure

```
Enterprise-AI-Data-Extractor/
│
├── scraper.py          # Async Playwright scraping engine with anti-bot evasion
├── ai_parser.py        # Langchain + Ollama structured output parser (Pydantic)
├── api.py              # FastAPI REST backend — /scrape, /export, /health
├── main.py             # Streamlit interactive frontend
├── requirements.txt    # Python dependencies
├── .gitignore
└── README.md
```

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Scraping** | Playwright (async) | Headless browser with JS rendering |
| **Anti-Bot** | Custom stealth scripts | UA rotation, viewport randomization, webdriver override |
| **AI/LLM** | Langchain + ChatOllama | LLM orchestration with structured output |
| **Model** | Llama 3.2 (via Ollama) | Local, private, no API costs |
| **Validation** | Pydantic v2 | Schema enforcement on LLM output |
| **Backend** | FastAPI + Uvicorn | Async REST API |
| **Frontend** | Streamlit | Rapid prototyping UI |
| **Parsing** | BeautifulSoup4 + lxml | DOM cleaning and text extraction |

---

## 🔒 Privacy & Cost

- **100% Local** — Ollama runs the LLM on your machine. No data leaves your network.
- **Zero API Costs** — No OpenAI/Anthropic API keys needed. No per-token billing.
- **Your Data, Your Control** — Ideal for sensitive or proprietary data extraction.

---

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 👤 Author

**Youssef Ashraf**
- GitHub: [@youssefashraf](https://github.com/YoussefAshraf711)

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**⭐ If this project helped you, consider giving it a star! ⭐**

</div>
