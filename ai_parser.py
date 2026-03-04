"""
Enterprise AI Data Extractor — AI Parsing Layer
Langchain + ChatOllama with Pydantic structured output.
"""

import asyncio
import logging
from typing import Optional

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field, ValidationError
from langchain_core.exceptions import OutputParserException

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic schemas for structured output
# ---------------------------------------------------------------------------
class ExtractedItem(BaseModel):
    """A single key-value data point extracted from a web page."""

    name: str = Field(description="Short label describing the extracted data point")
    value: str = Field(description="The actual extracted value")
    context: Optional[str] = Field(
        default=None,
        description="Optional surrounding context or category for the data point",
    )


class ExtractedData(BaseModel):
    """Container for all items extracted from a DOM chunk."""

    items: list[ExtractedItem] = Field(
        default_factory=list,
        description="List of extracted data points",
    )


# ---------------------------------------------------------------------------
# Prompt
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = (
    "You are a precise data-extraction assistant. "
    "Given raw text content from a web page, extract ONLY the information "
    "that matches the user's description. "
    "Return the data as a structured JSON object. "
    "Do NOT fabricate data. If nothing matches, return an empty items list."
)

HUMAN_PROMPT = (
    "Web page content:\n"
    "---\n"
    "{dom_content}\n"
    "---\n\n"
    "Extraction instruction: {parse_description}\n\n"
    "Extract all matching data points as structured items."
)

_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        ("human", HUMAN_PROMPT),
    ]
)


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------
MAX_RETRIES = 2


def _build_chain():
    """Build the Langchain chain with structured output."""
    llm = ChatOllama(
        model="llama3.2",
        temperature=0,
        format="json",
    )
    structured_llm = llm.with_structured_output(ExtractedData)
    return _prompt | structured_llm


async def parse_with_ollama(
    dom_chunks: list[str],
    parse_description: str,
) -> ExtractedData:
    """
    Send each DOM chunk to the LLM and aggregate results into a single
    ``ExtractedData`` object.

    Implements retry logic for validation / parsing errors (hallucination
    guard).

    Parameters
    ----------
    dom_chunks : list[str]
        Text chunks produced by ``split_dom_content``.
    parse_description : str
        Natural-language description of what to extract.

    Returns
    -------
    ExtractedData
        Aggregated extraction result.

    Raises
    ------
    RuntimeError
        If the LLM fails to produce valid output after retries.
    """
    chain = _build_chain()
    all_items: list[ExtractedItem] = []

    for idx, chunk in enumerate(dom_chunks, start=1):
        attempt = 0
        while attempt < MAX_RETRIES:
            try:
                result: ExtractedData = await chain.ainvoke(
                    {
                        "dom_content": chunk,
                        "parse_description": parse_description,
                    }
                )
                all_items.extend(result.items)
                logger.info(
                    "Parsed chunk %d/%d — %d items extracted",
                    idx,
                    len(dom_chunks),
                    len(result.items),
                )
                break  # success

            except (ValidationError, OutputParserException) as exc:
                attempt += 1
                logger.warning(
                    "LLM returned invalid output on chunk %d (attempt %d/%d): %s",
                    idx,
                    attempt,
                    MAX_RETRIES,
                    exc,
                )
                if attempt >= MAX_RETRIES:
                    raise RuntimeError(
                        f"LLM failed to produce valid structured output after "
                        f"{MAX_RETRIES} attempts on chunk {idx}. "
                        f"Last error: {exc}"
                    ) from exc

            except Exception as exc:
                logger.error("Unexpected error on chunk %d: %s", idx, exc)
                raise RuntimeError(
                    f"AI parsing failed on chunk {idx}: {exc}"
                ) from exc

    return ExtractedData(items=all_items)
