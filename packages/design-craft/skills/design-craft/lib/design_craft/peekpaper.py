"""Bounded Peekpaper source adapter for visual-reference discovery."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .reference_contract import CARD_SCHEMA, CATALOG_SCHEMA


PEEKPAPER_HOST = "peekpaper.com"
ISSUE_URL_TEMPLATE = "https://peekpaper.com/content/editions/{year}/{month}/{day}.json"
POST_URL_TEMPLATE = "https://peekpaper.com/{year}/{month}/{day}/{slug}"
POLICY_URL = "https://peekpaper.com/robots.txt"
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
MAX_POSTS_PER_ISSUE = 12
MAX_DESCRIPTION_LENGTH = 1000
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")


class PeekpaperError(ValueError):
    """Raised when source data violates the bounded adapter contract."""


class PeekpaperFetchError(RuntimeError):
    """Raised when the explicit network source cannot be fetched safely."""


class _RejectRedirects(HTTPRedirectHandler):
    def redirect_request(
        self,
        req: Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> None:
        return None


@dataclass(frozen=True)
class IssueSource:
    issue_date: str
    raw: bytes


def validate_issue_date(raw: str) -> date:
    if not DATE_PATTERN.fullmatch(raw):
        raise PeekpaperError(f"invalid Peekpaper issue date: {raw!r}")
    try:
        return date.fromisoformat(raw)
    except ValueError as exc:
        raise PeekpaperError(f"invalid Peekpaper issue date: {raw!r}") from exc


def issue_url(issue_date: str) -> str:
    parsed = validate_issue_date(issue_date)
    return ISSUE_URL_TEMPLATE.format(
        year=f"{parsed.year:04d}", month=f"{parsed.month:02d}", day=f"{parsed.day:02d}"
    )


def post_url(issue_date: str, slug: str) -> str:
    parsed = validate_issue_date(issue_date)
    if not SLUG_PATTERN.fullmatch(slug):
        raise PeekpaperError(f"invalid Peekpaper post slug: {slug!r}")
    return POST_URL_TEMPLATE.format(
        year=f"{parsed.year:04d}",
        month=f"{parsed.month:02d}",
        day=f"{parsed.day:02d}",
        slug=slug,
    )


def fetch_issue(issue_date: str, *, timeout_seconds: float = 10.0) -> IssueSource:
    url = issue_url(issue_date)
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "design-craft-visual-reference/1",
        },
        method="GET",
    )
    opener = build_opener(_RejectRedirects())
    try:
        with opener.open(request, timeout=timeout_seconds) as response:
            content_type = response.headers.get_content_type()
            if content_type != "application/json":
                raise PeekpaperFetchError(
                    f"Peekpaper issue returned unexpected content type: {content_type}"
                )
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise PeekpaperFetchError(f"failed to fetch {url}: {exc}") from exc
    if len(raw) > MAX_RESPONSE_BYTES:
        raise PeekpaperFetchError(
            f"Peekpaper issue exceeds {MAX_RESPONSE_BYTES} byte response limit"
        )
    return IssueSource(issue_date=issue_date, raw=raw)


def load_issue_fixture(fixture_dir: Path, issue_date: str) -> IssueSource:
    validate_issue_date(issue_date)
    path = fixture_dir / f"{issue_date}.json"
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise PeekpaperFetchError(f"failed to read Peekpaper fixture {path}: {exc}") from exc
    if len(raw) > MAX_RESPONSE_BYTES:
        raise PeekpaperFetchError(
            f"Peekpaper fixture exceeds {MAX_RESPONSE_BYTES} byte response limit: {path}"
        )
    return IssueSource(issue_date=issue_date, raw=raw)


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for key, value in pairs:
        if key in payload:
            raise PeekpaperError(f"duplicate JSON key: {key}")
        payload[key] = value
    return payload


def _decode_issue(source: IssueSource) -> dict[str, Any]:
    try:
        payload = json.loads(source.raw.decode("utf-8"), object_pairs_hook=_unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PeekpaperError(f"invalid Peekpaper JSON for {source.issue_date}: {exc}") from exc
    if not isinstance(payload, dict):
        raise PeekpaperError(f"Peekpaper issue {source.issue_date} must be an object")
    if payload.get("date") != source.issue_date:
        raise PeekpaperError(
            f"Peekpaper issue date mismatch: expected {source.issue_date}, got {payload.get('date')!r}"
        )
    posts = payload.get("posts")
    if not isinstance(posts, list):
        raise PeekpaperError(f"Peekpaper issue {source.issue_date} posts must be an array")
    if len(posts) > MAX_POSTS_PER_ISSUE:
        raise PeekpaperError(
            f"Peekpaper issue {source.issue_date} exceeds {MAX_POSTS_PER_ISSUE} posts"
        )
    count = payload.get("count")
    if not isinstance(count, int) or isinstance(count, bool) or count != len(posts):
        raise PeekpaperError(
            f"Peekpaper issue {source.issue_date} count must equal posts length"
        )
    return payload


def _required_string(value: Any, path: str, *, max_length: int = 500) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PeekpaperError(f"{path} must be a non-empty string")
    if len(value) > max_length:
        raise PeekpaperError(f"{path} exceeds {max_length} characters")
    return value


def _image_evidence(
    images: dict[str, Any], kind: str, canonical_post_url: str, captured_at: str
) -> dict[str, Any]:
    available = bool(images.get(kind))
    width = images.get("w")
    height = images.get("h")
    dimensions = (
        f"{width}x{height}"
        if isinstance(width, int)
        and not isinstance(width, bool)
        and isinstance(height, int)
        and not isinstance(height, bool)
        else "unreported"
    )
    notes = (
        f"Peekpaper {kind} capture is present; dimensions={dimensions}; "
        f"captured_at={captured_at or 'unreported'}."
        if available
        else f"Peekpaper {kind} capture is unavailable."
    )
    return {
        "status": "observed" if available else "unavailable",
        "evidence_refs": [canonical_post_url] if available else [],
        "notes": notes,
    }


def normalize_issue(source: IssueSource, *, observed_at: str) -> list[dict[str, Any]]:
    validate_issue_date(observed_at)
    payload = _decode_issue(source)
    source_sha256 = hashlib.sha256(source.raw).hexdigest()
    positions: set[int] = set()
    cards: list[tuple[int, dict[str, Any]]] = []
    for index, item in enumerate(payload["posts"]):
        path = f"Peekpaper issue {source.issue_date} posts[{index}]"
        if not isinstance(item, dict):
            raise PeekpaperError(f"{path} must be an object")
        slug = _required_string(item.get("slug"), f"{path}.slug", max_length=120)
        if not SLUG_PATTERN.fullmatch(slug):
            raise PeekpaperError(f"{path}.slug is invalid")
        position = item.get("position")
        if not isinstance(position, int) or isinstance(position, bool) or position < 0:
            raise PeekpaperError(f"{path}.position must be a non-negative integer")
        if position in positions:
            raise PeekpaperError(f"{path}.position duplicates {position}")
        positions.add(position)
        domain = _required_string(item.get("domain"), f"{path}.domain", max_length=253).lower()
        origin_url = _required_string(item.get("url"), f"{path}.url", max_length=2000)
        title = _required_string(item.get("title"), f"{path}.title", max_length=300)
        description = item.get("description", "")
        if not isinstance(description, str):
            raise PeekpaperError(f"{path}.description must be a string")
        if len(description) > MAX_DESCRIPTION_LENGTH:
            description = description[:MAX_DESCRIPTION_LENGTH]
        images = item.get("images")
        if not isinstance(images, dict):
            images = {}
        captured_at = item.get("capturedAt")
        captured_at_text = captured_at if isinstance(captured_at, str) else ""
        canonical_post_url = post_url(source.issue_date, slug)
        card = {
            "schema": CARD_SCHEMA,
            "id": f"peekpaper-{source.issue_date}-{slug}",
            "status": "candidate",
            "source": {
                "provider": "peekpaper",
                "issue_date": source.issue_date,
                "post_url": canonical_post_url,
                "observed_at": observed_at,
                "source_sha256": source_sha256,
            },
            "origin": {
                "url": origin_url,
                "domain": domain,
                "title": title,
                "source_description": description,
            },
            "classification": {
                "source_surface": "unclassified",
                "product_archetype": "unclassified",
                "reference_roles": [],
                "recommended_surface_modes": [],
                "blocked_surface_modes": [],
            },
            "evidence": {
                "desktop": _image_evidence(
                    images, "desktop", canonical_post_url, captured_at_text
                ),
                "mobile": _image_evidence(
                    images, "mobile", canonical_post_url, captured_at_text
                ),
                "origin_live": {
                    "status": "unverified",
                    "evidence_refs": [],
                    "notes": "Origin runtime has not been audited.",
                },
                "interaction": {
                    "status": "unverified",
                    "evidence_refs": [],
                    "notes": "Static source evidence cannot prove interaction behavior.",
                },
                "accessibility": {
                    "status": "unverified",
                    "evidence_refs": [],
                    "notes": "Static source evidence cannot prove accessibility.",
                },
                "performance": {
                    "status": "unverified",
                    "evidence_refs": [],
                    "notes": "Static source evidence cannot prove performance.",
                },
            },
            "observations": [],
            "transferable_mechanisms": [],
            "do_not_copy": [],
            "not_suitable_when": [],
            "project_validation_refs": [],
            "rights": {
                "mode": "reference-only",
                "ai_training": False,
                "assets_redistributed": False,
                "policy_url": POLICY_URL,
                "policy_observed_at": observed_at,
            },
            "lifecycle": {"reviewed_at": None, "review_after": None},
        }
        cards.append((position, card))
    return [card for _, card in sorted(cards, key=lambda pair: pair[0])]


def build_catalog(sources: Iterable[IssueSource], *, observed_at: str) -> dict[str, Any]:
    validate_issue_date(observed_at)
    source_list = sorted(sources, key=lambda source: source.issue_date)
    if not source_list:
        raise PeekpaperError("at least one Peekpaper issue is required")
    issue_dates = [source.issue_date for source in source_list]
    if len(issue_dates) != len(set(issue_dates)):
        raise PeekpaperError("Peekpaper issue dates must be unique")
    cards: list[dict[str, Any]] = []
    for source in source_list:
        cards.extend(normalize_issue(source, observed_at=observed_at))
    card_ids = [str(card["id"]) for card in cards]
    if len(card_ids) != len(set(card_ids)):
        raise PeekpaperError("normalized Peekpaper card ids must be unique")
    catalog_id = "peekpaper-" + "--".join(issue_dates)
    return {
        "schema": CATALOG_SCHEMA,
        "id": catalog_id,
        "title": "Peekpaper visual reference pilot: " + ", ".join(issue_dates),
        "observed_at": observed_at,
        "source_policy": {
            "policy_url": POLICY_URL,
            "policy_observed_at": observed_at,
            "mode": "reference-only",
            "ai_training": False,
            "assets_redistributed": False,
        },
        "cards": cards,
        "hypotheses": [],
    }
