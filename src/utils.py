"""Shared utilities for the Job Seeker AI Toolkit."""

import logging
import random
import re
import time
from datetime import date
from pathlib import Path
from typing import Any, Callable
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import httpx
import yaml
from trafilatura import extract, fetch_url


def setup_logging(name: str) -> logging.Logger:
    """Configure and return a logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(name)s] %(levelname)s: %(message)s")
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def load_yaml(path: str | Path) -> dict | list:
    """Load a YAML file and return its contents.

    Returns empty dict if file is missing or contains corrupt YAML.
    """
    logger = logging.getLogger("utils")
    path = Path(path)
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8", newline="\n") as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        logger.error(f"Corrupt YAML in {path}: {e}")
        return {}


def save_yaml(path: str | Path, data: dict | list) -> None:
    """Save data to a YAML file. Uses LF line endings to prevent Windows CRLF issues."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def retry_with_backoff(
    fn: Callable[[], Any],
    max_retries: int = 3,
    base_delay: float = 2.0,
    retryable_exceptions: tuple = (Exception,),
    logger: logging.Logger | None = None,
) -> Any:
    """Call fn() with exponential backoff on retryable exceptions."""
    log = logger or logging.getLogger("utils.retry")
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return fn()
        except retryable_exceptions as e:
            last_exception = e
            if attempt < max_retries:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                log.warning(
                    f"Attempt {attempt + 1}/{max_retries + 1} failed: {e}. "
                    f"Retrying in {delay:.1f}s..."
                )
                time.sleep(delay)
            else:
                log.error(f"All {max_retries + 1} attempts failed. Last error: {e}")
        except Exception:
            raise

    raise last_exception


# Tracking params to strip during URL normalization
_TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "ref", "source", "mc_cid", "mc_eid",
}


def normalize_url(url: str) -> str:
    """Normalize a URL for deduplication."""
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    path = parsed.path.rstrip("/")
    if parsed.query:
        params = parse_qs(parsed.query, keep_blank_values=True)
        filtered = {k: v for k, v in params.items() if k.lower() not in _TRACKING_PARAMS}
        query = urlencode(filtered, doseq=True)
    else:
        query = ""
    return urlunparse((scheme, netloc, path, parsed.params, query, ""))


_COMPANY_SUFFIXES = re.compile(
    r"[,.]?\s*\b(inc|incorporated|llc|ltd|limited|corp|corporation|co|"
    r"company|group|holdings|plc|gmbh|ag|sa)\b\.?",
    re.IGNORECASE,
)
_COMPANY_DOMAIN_SUFFIXES = re.compile(r"\.(com|io|ai|co|org|net)$", re.IGNORECASE)


def _normalize_company(name: str) -> str:
    """Strip common corporate and domain suffixes for comparison."""
    cleaned = _COMPANY_SUFFIXES.sub("", name)
    cleaned = _COMPANY_DOMAIN_SUFFIXES.sub("", cleaned)
    cleaned = cleaned.strip(" ,.")
    return cleaned.lower() if cleaned else name.lower()


def resolve_company_name(
    raw_name: str,
    known_names: list[str],
    threshold: int = 85,
    token_set_threshold: int = 95,
) -> tuple[str | None, float]:
    """Resolve a company name against known names using fuzzy matching.

    Returns (matched_name, confidence_score) or (None, 0.0).
    """
    from rapidfuzz import fuzz

    if not known_names or not raw_name.strip():
        return None, 0.0

    raw_lower = raw_name.strip().lower()
    raw_normalized = _normalize_company(raw_name)

    for known in known_names:
        if known.lower() == raw_lower:
            return known, 100.0

    for known in known_names:
        if _normalize_company(known) == raw_normalized and raw_normalized:
            return known, 99.0

    best_match = None
    best_score = 0.0
    tied = False

    for known in known_names:
        known_normalized = _normalize_company(known)
        tsr = fuzz.token_set_ratio(raw_normalized, known_normalized)
        min_norm_len = min(len(raw_normalized), len(known_normalized))
        if tsr >= token_set_threshold and min_norm_len > 3 and tsr > best_score:
            best_match = known
            best_score = tsr
            tied = False
        elif tsr >= token_set_threshold and min_norm_len > 3 and tsr == best_score and best_match != known:
            tied = True

        min_len = min(len(raw_normalized), len(known_normalized))
        max_len = max(len(raw_normalized), len(known_normalized))
        if max_len > 0 and min_len / max_len >= 0.5:
            sr = fuzz.ratio(raw_normalized, known_normalized)
            if sr >= threshold and sr > best_score:
                best_match = known
                best_score = sr
                tied = False
            elif sr >= threshold and sr == best_score and best_match != known:
                tied = True

    if tied:
        return None, 0.0
    if best_match:
        return best_match, best_score
    return None, 0.0


def fetch_page_text(url: str) -> str | None:
    """Fetch a URL and extract readable text content.

    Uses trafilatura first, falls back to httpx + BeautifulSoup.
    """
    logger = setup_logging("utils.fetch")

    try:
        downloaded = fetch_url(url)
        if downloaded:
            text = extract(downloaded, include_comments=False, include_tables=True)
            if text and len(text) > 200:
                logger.info(f"Extracted {len(text)} chars via trafilatura from {url}")
                return text
    except Exception as e:
        logger.warning(f"Trafilatura failed for {url}: {e}")

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = httpx.get(url, headers=headers, follow_redirects=True, timeout=30)
        response.raise_for_status()
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        if text and len(text) > 200:
            logger.info(f"Extracted {len(text)} chars via BeautifulSoup from {url}")
            return text
    except Exception as e:
        logger.warning(f"HTTP fallback failed for {url}: {e}")

    logger.error(f"Could not extract text from {url}")
    return None


def extract_urls(text: str) -> list[str]:
    """Extract URLs from text (for email body parsing)."""
    url_pattern = re.compile(r'https?://[^\s<>"\')\]]+', re.IGNORECASE)
    urls = url_pattern.findall(text)
    cleaned = []
    for url in urls:
        url = url.rstrip(".,;:!?)")
        if len(url) > 10:
            cleaned.append(url)
    return list(dict.fromkeys(cleaned))


def detect_source(url: str) -> str:
    """Detect the listing source from a URL."""
    url_lower = url.lower()
    if "linkedin.com" in url_lower:
        return "linkedin"
    elif "indeed.com" in url_lower:
        return "indeed"
    elif "/careers" in url_lower or "/jobs" in url_lower:
        return "careers_page"
    return "other"


def get_email_body(msg) -> str:
    """Extract plain text body from an email message object.

    Handles multipart messages, prefers text/plain over text/html.
    Consolidated from ingestor.py and feedback.py.
    """
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode("utf-8", errors="replace")
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            return payload.decode("utf-8", errors="replace")
    return ""


_MONTH_MAP = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
}

_BODY_DATE_RE = re.compile(
    r"Job\s+posted\s+on\s+([A-Za-z]+)\s+(\d{1,2}),\s+(\d{4})",
    re.IGNORECASE,
)

_BODY_COMPANY_RE = re.compile(
    r"(?:ABOUT|About)\s+([A-Z][^\n]+?)(?:\s+and\s+[A-Z]|\s*\n)",
)


def parse_job_body_date(body_text: str) -> date | None:
    """Extract original posting date from Indeed job body text."""
    match = _BODY_DATE_RE.search(body_text)
    if not match:
        return None
    month_str, day_str, year_str = match.group(1), match.group(2), match.group(3)
    month = _MONTH_MAP.get(month_str.lower())
    if not month:
        return None
    try:
        return date(int(year_str), month, int(day_str))
    except ValueError:
        return None


def parse_job_body_company(body_text: str) -> str | None:
    """Extract the real company name from Indeed job body text."""
    match = _BODY_COMPANY_RE.search(body_text)
    if not match:
        return None
    return match.group(1).strip()


def suggest_queries(profile_path: str | Path) -> list[dict[str, str]]:
    """Generate Indeed search query suggestions from user profile."""
    profile = load_yaml(profile_path)
    if not profile:
        return []

    roles = profile.get("target_roles", [])
    location = profile.get("location", "Singapore")
    keywords = []

    minimum_bar = profile.get("company_preferences", {}).get("minimum_bar", [])
    for pref in minimum_bar:
        if "ai" in pref.lower():
            keywords.append("AI")
            break

    queries = []
    for role in roles:
        queries.append({"search": role, "location": location})
        for kw in keywords:
            queries.append({"search": f"{role} {kw}", "location": location})
        queries.append({"search": role, "location": "remote"})

    return queries
