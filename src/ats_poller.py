"""ATS watchlist poller: fetches fresh listings from public job-board APIs.

Polls the public, unauthenticated JSON endpoints that Greenhouse, Lever, and
Ashby publish for every hosted job board, for each company on the user's
watchlist (data/target_companies.yaml). New listings are queued into
input_listings.yaml with prefetched_text so scoring never needs a page fetch.

Also provides ATS auto-detection: given a company name, probe each provider
for likely board tokens and record the first hit on the watchlist.
"""

import argparse
import html
import re
import sys
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

import httpx

from src.utils import (
    _normalize_company,
    load_yaml,
    normalize_url,
    resolve_company_name,
    retry_with_backoff,
    save_yaml,
    setup_logging,
)

logger = setup_logging("ats_poller")

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}

# Pause between board fetches — one request per company per run is already
# light, but stay polite to the ATS providers.
POLL_DELAY_SECONDS = 1.0

# Scout truncates listing text to 8000 chars before scoring; storing more
# than that in input_listings.yaml just bloats the file.
MAX_PREFETCHED_CHARS = 8000

WATCHLIST_FILE = "target_companies.yaml"


class _RetryableHTTPError(Exception):
    """429/5xx responses worth retrying; 4xx like 404 means 'no such board'."""


def _fetch_json(url: str) -> Any | None:
    """GET a JSON endpoint with retry on transient failures.

    Returns the parsed payload, or None on 404/non-JSON/persistent failure.
    """

    def _get() -> httpx.Response:
        r = httpx.get(url, headers=_HEADERS, follow_redirects=True, timeout=30)
        if r.status_code == 429 or r.status_code >= 500:
            raise _RetryableHTTPError(f"HTTP {r.status_code} from {url}")
        return r

    try:
        response = retry_with_backoff(
            fn=_get,
            max_retries=2,
            base_delay=2.0,
            retryable_exceptions=(httpx.TransportError, _RetryableHTTPError),
            logger=logger,
        )
    except Exception as e:
        logger.warning(f"Fetch failed for {url}: {e}")
        return None

    if response.status_code != 200:
        return None
    try:
        return response.json()
    except ValueError:
        logger.warning(f"Non-JSON response from {url}")
        return None


def _strip_html(html_text: str) -> str:
    """Convert an HTML job description to readable plain text."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html.unescape(html_text), "html.parser")
    return soup.get_text(separator="\n", strip=True)


def _parse_when(value: Any) -> date | None:
    """Parse a posting timestamp: ms epoch (Lever) or ISO 8601 (Greenhouse/Ashby)."""
    if value is None:
        return None
    try:
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value / 1000, tz=timezone.utc).date()
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except (ValueError, OverflowError, OSError):
        return None
    return None


@dataclass
class Candidate:
    """One job posting pulled from an ATS board, ready for the scoring queue."""

    url: str
    company_name: str
    role_title: str
    location: str | None = None
    posted_at: date | None = None
    description_text: str = ""

    def prefetched_text(self) -> str:
        parts = [self.role_title, f"Company: {self.company_name}"]
        if self.location:
            parts.append(f"Location: {self.location}")
        if self.posted_at:
            parts.append(f"Posted: {self.posted_at.isoformat()}")
        parts.append("")
        parts.append(self.description_text)
        return "\n".join(parts)[:MAX_PREFETCHED_CHARS]


# --- Provider adapters -------------------------------------------------------
#
# Each provider exposes a public job-board JSON endpoint keyed by a board
# token (the company's slug on that ATS). parse() receives the raw payload
# and the watchlist display name, and returns Candidates.


def _greenhouse_board_url(token: str) -> str:
    return f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"


def _greenhouse_parse(payload: Any, company: str) -> list[Candidate]:
    candidates = []
    for job in (payload or {}).get("jobs", []):
        url = job.get("absolute_url")
        title = job.get("title")
        if not url or not title:
            continue
        content = job.get("content") or ""
        candidates.append(Candidate(
            url=url,
            company_name=company,
            role_title=title,
            location=(job.get("location") or {}).get("name"),
            posted_at=_parse_when(job.get("first_published") or job.get("updated_at")),
            description_text=_strip_html(content) if content else "",
        ))
    return candidates


def _greenhouse_org_name(token: str) -> str | None:
    board = _fetch_json(f"https://boards-api.greenhouse.io/v1/boards/{token}")
    if isinstance(board, dict):
        return board.get("name")
    return None


def _lever_board_url(token: str) -> str:
    return f"https://api.lever.co/v0/postings/{token}?mode=json"


def _lever_parse(payload: Any, company: str) -> list[Candidate]:
    if not isinstance(payload, list):
        return []
    candidates = []
    for job in payload:
        url = job.get("hostedUrl")
        title = job.get("text")
        if not url or not title:
            continue
        categories = job.get("categories") or {}
        description = job.get("descriptionPlain") or ""
        for lst in job.get("lists") or []:
            section = lst.get("text") or ""
            body = _strip_html(lst.get("content") or "")
            if body:
                description += f"\n\n{section}\n{body}"
        candidates.append(Candidate(
            url=url,
            company_name=company,
            role_title=title,
            location=categories.get("location"),
            posted_at=_parse_when(job.get("createdAt")),
            description_text=description,
        ))
    return candidates


def _ashby_board_url(token: str) -> str:
    return f"https://api.ashbyhq.com/posting-api/job-board/{token}"


def _ashby_parse(payload: Any, company: str) -> list[Candidate]:
    candidates = []
    for job in (payload or {}).get("jobs", []):
        url = job.get("jobUrl") or job.get("applyUrl")
        title = job.get("title")
        if not url or not title:
            continue
        # Ashby only lists published postings; isListed=False means hidden.
        if job.get("isListed") is False:
            continue
        description = job.get("descriptionPlain") or ""
        if not description and job.get("descriptionHtml"):
            description = _strip_html(job["descriptionHtml"])
        candidates.append(Candidate(
            url=url,
            company_name=company,
            role_title=title,
            location=job.get("location"),
            posted_at=_parse_when(job.get("publishedAt")),
            description_text=description,
        ))
    return candidates


def _payload_has_jobs(payload: Any) -> bool:
    if isinstance(payload, list):
        return True  # Lever returns a bare array (may legitimately be empty)
    return isinstance(payload, dict) and "jobs" in payload


@dataclass(frozen=True)
class Provider:
    name: str
    board_url: Callable[[str], str]
    parse: Callable[[Any, str], list[Candidate]]
    org_name: Callable[[str], "str | None"] | None = None  # takes board token


PROVIDERS: dict[str, Provider] = {
    "greenhouse": Provider("greenhouse", _greenhouse_board_url, _greenhouse_parse,
                           org_name=_greenhouse_org_name),
    "lever": Provider("lever", _lever_board_url, _lever_parse),
    "ashby": Provider("ashby", _ashby_board_url, _ashby_parse),
}


# --- Slug + title matching ---------------------------------------------------


def candidate_slugs(company_name: str) -> list[str]:
    """Generate likely board tokens for a company name, most-likely first."""
    slugs: list[str] = []
    for base in (company_name, _normalize_company(company_name)):
        words = re.findall(r"[a-z0-9]+", base.lower())
        if not words:
            continue
        for slug in ("".join(words), "-".join(words)):
            if slug not in slugs:
                slugs.append(slug)
    return slugs


_SENIORITY_WORDS = {
    "senior", "sr", "junior", "jr", "lead", "principal", "staff", "head",
    "associate", "assistant", "intern", "of", "the", "a", "an",
}


def title_matches(title: str, target_roles: list[str]) -> bool:
    """True if a job title matches any target role.

    A role matches when it appears verbatim in the title, or when every
    non-seniority word of the role appears somewhere in the title (so
    "Growth Marketing Manager" matches "Marketing Manager, Growth").
    """
    title_lower = title.lower()
    title_tokens = set(re.findall(r"[a-z0-9]+", title_lower))
    for role in target_roles:
        role_lower = role.lower().strip()
        if not role_lower:
            continue
        if role_lower in title_lower:
            return True
        core = [w for w in re.findall(r"[a-z0-9]+", role_lower)
                if w not in _SENIORITY_WORDS]
        if core and all(w in title_tokens for w in core):
            return True
    return False


# --- Poller ------------------------------------------------------------------


class ATSPoller:
    """Polls ATS job boards for watchlist companies and queues new listings."""

    def __init__(self, config_dir: Path | None = None, data_dir: Path | None = None):
        self.config_dir = config_dir or (Path.cwd() / "config")
        self.data_dir = data_dir or (Path.cwd() / "data")

    # -- watchlist --

    def load_watchlist(self) -> dict:
        data = load_yaml(self.data_dir / WATCHLIST_FILE)
        # `or not data["companies"]` also catches a bare `companies:` key
        # (YAML null) — iterating None would raise a raw TypeError
        if not data or not data.get("companies"):
            data = {"companies": []}
        return data

    def save_watchlist(self, data: dict) -> None:
        save_yaml(self.data_dir / WATCHLIST_FILE, data)

    def add_company(self, name: str, ats: str, board_token: str,
                    source: str = "auto_detected") -> bool:
        """Add a company to the watchlist. Returns False if already present."""
        watchlist = self.load_watchlist()
        for entry in watchlist["companies"]:
            if entry.get("ats") == ats and entry.get("board_token") == board_token:
                logger.info(f"{name} already on watchlist ({ats}/{board_token})")
                return False
        watchlist["companies"].append({
            "name": name,
            "ats": ats,
            "board_token": board_token,
            "added": str(date.today()),
            "source": source,
        })
        self.save_watchlist(watchlist)
        logger.info(f"Added {name} to watchlist ({ats}/{board_token})")
        return True

    # -- detection --

    def detect_company(self, name: str) -> dict | None:
        """Probe each provider for a company's board token.

        Returns {"ats", "board_token", "detected_name", "jobs_count"} for the
        first provider that responds with a job board, or None. The equivalent
        of checking whether a company "has supported public endpoints".
        """
        slugs = candidate_slugs(name)
        if not slugs:
            return None
        for provider in PROVIDERS.values():
            for slug in slugs:
                payload = _fetch_json(provider.board_url(slug))
                if payload is None or not _payload_has_jobs(payload):
                    continue

                detected_name = None
                if provider.org_name:
                    detected_name = provider.org_name(slug)
                if detected_name:
                    matched, confidence = resolve_company_name(detected_name, [name])
                    if matched is None:
                        logger.info(
                            f"{provider.name}/{slug} exists but is named "
                            f"'{detected_name}' — not a match for '{name}', skipping"
                        )
                        continue

                jobs = provider.parse(payload, detected_name or name)
                logger.info(
                    f"Detected {name} on {provider.name} "
                    f"(token: {slug}, {len(jobs)} open jobs)"
                )
                return {
                    "ats": provider.name,
                    "board_token": slug,
                    "detected_name": detected_name,
                    "jobs_count": len(jobs),
                }
        logger.info(f"No supported ATS found for '{name}' (tried {', '.join(slugs)})")
        return None

    # -- polling --

    def _load_search_config(self) -> tuple[int, list[str]]:
        """Return (max_age_days, target_roles) from profile.yaml, with defaults.

        A corrupt profile raises CorruptYamlError (fail closed) — polling
        without a title filter queues entire boards and each queued listing
        costs a scoring API call downstream.
        """
        profile = load_yaml(self.config_dir / "profile.yaml") or {}
        max_age_days = (profile.get("search") or {}).get("max_age_days", 30)
        target_roles = profile.get("target_roles") or []
        return max_age_days, target_roles

    def poll(self, companies: list[str] | None = None,
             all_roles: bool = False, dry_run: bool = False) -> list[Candidate]:
        """Fetch each watchlist company's board and return filtered candidates.

        companies: optional list of watchlist names to poll (default: all).
            Names are matched exactly first, then fuzzily — /watch-company may
            have stored the provider's org name ("Stripe, Inc.") rather than
            what the user typed ("Stripe"). Raises LookupError if a requested
            name matches nothing.
        all_roles: skip the target-role title filter.
        dry_run: don't touch any state (no last_polled stamps, no save).
        """
        watchlist = self.load_watchlist()
        entries = [e for e in watchlist["companies"] or []
                   if e.get("ats") in PROVIDERS and e.get("board_token")]
        if companies:
            names = [e.get("name") or "" for e in entries]
            matched_names: set[str] = set()
            for requested in companies:
                exact = [n for n in names if n.lower() == requested.lower()]
                if exact:
                    matched_names.update(exact)
                    continue
                fuzzy, _ = resolve_company_name(requested, names)
                if fuzzy:
                    logger.info(f"Matched '{requested}' to watchlist entry '{fuzzy}'")
                    matched_names.add(fuzzy)
                else:
                    raise LookupError(
                        f"No watchlist entry matches '{requested}'. "
                        f"Run /watch-company to see the exact names on your watchlist."
                    )
            entries = [e for e in entries if (e.get("name") or "") in matched_names]

        if not entries:
            logger.info("No ATS-enabled companies on the watchlist — nothing to poll")
            return []

        max_age_days, target_roles = self._load_search_config()
        if not all_roles and not target_roles:
            # Fail closed: an absent/empty profile must not widen the poll to
            # every open job on every board (each queued listing costs a
            # scoring API call). --all-roles exists for the deliberate case.
            logger.error(
                "No target_roles found in profile.yaml — refusing to poll "
                "without a title filter. Run /setup (or the profile_setup "
                "workflow), or pass --all-roles to poll everything deliberately."
            )
            return []
        cutoff = date.today() - timedelta(days=max_age_days)

        candidates: list[Candidate] = []
        for i, entry in enumerate(entries):
            provider = PROVIDERS[entry["ats"]]
            name = entry.get("name") or entry["board_token"]
            payload = _fetch_json(provider.board_url(entry["board_token"]))
            if payload is None:
                logger.warning(f"Could not fetch {provider.name} board for {name}")
                continue

            jobs = provider.parse(payload, name)
            kept = []
            for job in jobs:
                if job.posted_at and job.posted_at < cutoff:
                    continue
                if not all_roles and target_roles and not title_matches(
                    job.role_title, target_roles
                ):
                    continue
                kept.append(job)
            logger.info(f"{name}: {len(jobs)} open jobs, {len(kept)} match filters")
            candidates.extend(kept)

            if not dry_run:
                # Date granularity, not seconds: the scheduled workflow commits
                # this file, and a per-second timestamp would produce a no-op
                # commit every single cron run
                entry["last_polled"] = str(date.today())
            if i < len(entries) - 1:
                time.sleep(POLL_DELAY_SECONDS)

        if not dry_run:
            self.save_watchlist(watchlist)
        return candidates

    # -- pipeline handoff --

    def append_candidates(self, candidates: list[Candidate]) -> int:
        """Queue new candidates into input_listings.yaml, deduping against
        both input and processed listings. Returns count added."""
        input_path = self.data_dir / "input_listings.yaml"
        processed_path = self.data_dir / "processed_listings.yaml"

        input_data = load_yaml(input_path)
        if not input_data or not input_data.get("listings"):
            input_data = {"listings": []}
        processed_data = load_yaml(processed_path)
        if not processed_data or not processed_data.get("listings"):
            processed_data = {"listings": []}

        existing_urls = {normalize_url(l.get("url", "")) for l in input_data["listings"]}
        existing_urls.update(
            normalize_url(l.get("url", "")) for l in processed_data["listings"]
        )

        added = 0
        for candidate in candidates:
            normalized = normalize_url(candidate.url)
            if normalized in existing_urls:
                continue
            input_data["listings"].append({
                "url": candidate.url,
                "source": "ats",
                "date_added": str(date.today()),
                "status": "queued",
                "company_name": candidate.company_name,
                "role_title": candidate.role_title,
                "prefetched_text": candidate.prefetched_text(),
            })
            existing_urls.add(normalized)
            added += 1

        if added > 0:
            save_yaml(input_path, input_data)
            logger.info(f"Added {added} new listing(s) to input_listings.yaml")
        else:
            logger.info("No new listings to add (all duplicates)")
        return added

    def run(self, companies: list[str] | None = None, all_roles: bool = False,
            dry_run: bool = False) -> int:
        """Poll the watchlist and queue new candidates. Returns count added."""
        candidates = self.poll(companies=companies, all_roles=all_roles, dry_run=dry_run)
        if dry_run:
            for c in candidates:
                logger.info(f"[dry-run] {c.company_name} — {c.role_title} ({c.url})")
            return 0
        return self.append_candidates(candidates)


def main():
    parser = argparse.ArgumentParser(
        description="Poll public ATS job boards for watchlist companies"
    )
    parser.add_argument("--detect", metavar="COMPANY",
                        help="Detect a company's ATS and add it to the watchlist")
    parser.add_argument("--company", metavar="NAME",
                        help="Poll only this watchlist company")
    parser.add_argument("--all-roles", action="store_true",
                        help="Skip the target-role title filter")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show matching jobs without queueing them")
    args = parser.parse_args()

    poller = ATSPoller()

    if args.detect:
        result = poller.detect_company(args.detect)
        if result is None:
            print(f"No supported ATS (Greenhouse/Lever/Ashby) found for '{args.detect}'.")
            sys.exit(1)
        poller.add_company(
            result["detected_name"] or args.detect,
            result["ats"],
            result["board_token"],
        )
        print(
            f"✓ {result['detected_name'] or args.detect} uses {result['ats']} "
            f"(token: {result['board_token']}, {result['jobs_count']} open jobs) "
            f"— added to data/{WATCHLIST_FILE}"
        )
        return

    try:
        added = poller.run(
            companies=[args.company] if args.company else None,
            all_roles=args.all_roles,
            dry_run=args.dry_run,
        )
    except LookupError as e:
        print(str(e))
        sys.exit(1)
    if not args.dry_run:
        print(f"✓ Queued {added} new listing(s) — run `python -m src.scout` to score them")


if __name__ == "__main__":
    main()
