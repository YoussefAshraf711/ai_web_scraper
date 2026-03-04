"""
Enterprise AI Data Extractor — Streamlit Frontend
Connects to the FastAPI backend for scraping and data export.
"""

import streamlit as st
import requests
import json
import pandas as pd

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
API_BASE = "http://localhost:8000"

st.set_page_config(page_title="AI Data Extractor", page_icon="🔍", layout="wide")

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("🔍 Enterprise AI Data Extractor")
st.caption(
    "Powered by Playwright · Llama 3.2 · FastAPI — "
    "Enter a URL and describe what data to extract."
)

# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------
col1, col2 = st.columns([2, 1])
with col1:
    url = st.text_input("🌐 Website URL", placeholder="https://example.com")
with col2:
    st.markdown("<br>", unsafe_allow_html=True)

parse_description = st.text_area(
    "📝 What data should be extracted?",
    placeholder='e.g. "Extract all product names and prices"',
    height=100,
)

btn_col1, btn_col2, _ = st.columns([1, 1, 3])

# ---------------------------------------------------------------------------
# Scrape & Parse
# ---------------------------------------------------------------------------
with btn_col1:
    scrape_clicked = st.button("🚀 Scrape & Parse", type="primary", use_container_width=True)

with btn_col2:
    export_clicked = st.button("📥 Download CSV", use_container_width=True)


def _call_api(endpoint: str, url: str, description: str):
    """Call the FastAPI backend and handle errors."""
    try:
        resp = requests.post(
            f"{API_BASE}{endpoint}",
            json={"url": url, "parse_description": description},
            timeout=1800,
        )
        resp.raise_for_status()
        return resp
    except requests.ConnectionError:
        st.error(
            "⚠️ Cannot reach the FastAPI backend. "
            "Make sure it is running: `uvicorn api:app --port 8000`"
        )
    except requests.HTTPError as exc:
        detail = exc.response.json().get("detail", str(exc))
        st.error(f"❌ API error ({exc.response.status_code}): {detail}")
    except requests.Timeout:
        st.error("⏱️ Request timed out. The page may be too large or the LLM is slow.")
    return None


# --- Scrape button ---
if scrape_clicked:
    if not url or not parse_description:
        st.warning("Please provide both a URL and an extraction description.")
    else:
        with st.spinner("Scraping and parsing — this may take a moment…"):
            resp = _call_api("/scrape", url, parse_description)

        if resp is not None:
            data = resp.json()
            items = data.get("data", {}).get("items", [])

            st.session_state["last_result"] = data
            st.session_state["last_items"] = items

            st.success(f"✅ Extracted **{len(items)}** data points.")

            if items:
                df = pd.DataFrame(items)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No matching data found on the page.")

            with st.expander("Raw JSON response"):
                st.json(data)


# --- Export button ---
if export_clicked:
    if not url or not parse_description:
        st.warning("Please provide both a URL and an extraction description.")
    else:
        with st.spinner("Generating CSV export…"):
            resp = _call_api("/export", url, parse_description)

        if resp is not None:
            st.download_button(
                label="💾 Save CSV",
                data=resp.content,
                file_name="extracted_data.csv",
                mime="text/csv",
            )

# ---------------------------------------------------------------------------
# Persist previous results across re-renders
# ---------------------------------------------------------------------------
if "last_items" in st.session_state and not scrape_clicked:
    items = st.session_state["last_items"]
    if items:
        st.subheader("Previous Extraction")
        st.dataframe(pd.DataFrame(items), use_container_width=True)