"""
Enterprise AI Data Extractor — Scraping Engine
Async Playwright-based scraper with anti-bot evasion techniques.
"""

import asyncio
import random
import logging

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Anti-bot configuration
# ---------------------------------------------------------------------------
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.4; rv:125.0) Gecko/20100101 Firefox/125.0",
]

VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1366, "height": 768},
    {"width": 1536, "height": 864},
    {"width": 1440, "height": 900},
]

STEALTH_JS = """
// Remove navigator.webdriver flag
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

// Spoof plugins array
Object.defineProperty(navigator, 'plugins', {
    get: () => [1, 2, 3, 4, 5],
});

// Spoof languages
Object.defineProperty(navigator, 'languages', {
    get: () => ['en-US', 'en'],
});

// Override chrome runtime
window.chrome = { runtime: {} };
"""


# ---------------------------------------------------------------------------
# Core scraping function
# ---------------------------------------------------------------------------
async def scrape_website(
    url: str,
    *,
    timeout_ms: int = 30_000,
    wait_after_load_ms: int | None = None,
) -> str:
    """
    Launch a headless Chromium browser, navigate to *url*, and return the full
    page HTML source.  Uses anti-bot evasion (randomized UA / viewport /
    stealth JS) and configurable timeouts.

    Parameters
    ----------
    url : str
        Target page URL.
    timeout_ms : int
        Navigation timeout in milliseconds (default 30 s).
    wait_after_load_ms : int | None
        Optional extra wait after DOM load to let JS-rendered content appear.
        If ``None`` a random delay between 1–3 s is used.

    Returns
    -------
    str
        Full HTML source of the loaded page.

    Raises
    ------
    TimeoutError
        If the page did not load within *timeout_ms*.
    RuntimeError
        For any other Playwright failure.
    """
    ua = random.choice(USER_AGENTS)
    viewport = random.choice(VIEWPORTS)
    delay = wait_after_load_ms or random.randint(1000, 3000)

    logger.info("Scraping %s  (UA=%s, viewport=%s)", url, ua[:40], viewport)

    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=ua,
                viewport=viewport,
                locale="en-US",
                timezone_id="America/New_York",
                java_script_enabled=True,
            )

            page = await context.new_page()

            # Inject stealth script before any page JS runs
            await page.add_init_script(STEALTH_JS)

            await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)

            # Human-like delay to let dynamic content render
            await page.wait_for_timeout(delay)

            html = await page.content()

            await browser.close()

            logger.info("Scrape complete — %d bytes received", len(html))
            return html

    except PlaywrightTimeout as exc:
        msg = f"Timeout: page did not load within {timeout_ms} ms — {url}"
        logger.error(msg)
        raise TimeoutError(msg) from exc
    except Exception as exc:
        msg = f"Scraping failed for {url}: {exc}"
        logger.error(msg)
        raise RuntimeError(msg) from exc


# ---------------------------------------------------------------------------
# DOM helpers (kept synchronous — fast HTML parsing)
# ---------------------------------------------------------------------------
def extract_body_content(html_content: str) -> str:
    """Return the inner HTML of the ``<body>`` tag, or an empty string."""
    soup = BeautifulSoup(html_content, "html.parser")
    body = soup.body
    return str(body) if body else ""


def clean_body_content(body_content: str) -> str:
    """Strip ``<script>`` / ``<style>`` tags and collapse whitespace."""
    soup = BeautifulSoup(body_content, "html.parser")

    for tag in soup(["script", "style", "noscript", "svg", "iframe"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


def split_dom_content(dom_content: str, max_length: int = 10000) -> list[str]:
    """Chunk content into pieces of at most *max_length* characters."""
    return [
        dom_content[i : i + max_length]
        for i in range(0, len(dom_content), max_length)
    ]
